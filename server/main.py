"""Temporary single-file server implementation.

Current Target Algorithm:

Whenever changes occur:
    For each line $l deleted:
        If $l was legal:
            Delete the state entries related to $l
        Else:
            Mark $l as illegal
    For each line $l added:
        If $l is legal:
            Store entry parsed from $l
        Else:
            Mark $l as illegal
    For each line $l edited (probably at most 1):
        (Delay for a whle before proceeding, in case the user makes changes in quick succession)
        Update entry related to $l
        Update legality of $l

If the user hasn't edited for x seconds:
    Validate the entries for missing references, etc. and display the errors.

NOTE: need to think about way to deal with models in the future.
Idea: first try to correct the line. If that is not possible, ignore it. if it is has something
to do with brackets, e.g. start_model start_model, then do something intelligent like add end_model
before the second start_model.
Also: look at Jedi docs for inspiration

NOTE: still probably need dummy tokens, and a way to preserve the context
short-term TODO list
* definition
* handle models in error recovery
* display syntax error
* uniprot
* syntax highlighting?

NOTE: idea for optimization: for whatever change made in a range, only re-parse items in that range.
But if the change crosses model boundaries, need to extend the changed range to encompass the model
as well. Should be a good enough optimization for now.
"""
import os
import sys

EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(EXTENSION_ROOT, "pythonFiles", "lib", "python"))

from pygls.types import (CompletionItem, CompletionList, CompletionParams, Diagnostic,
                         DidChangeTextDocumentParams,
                         DidOpenTextDocumentParams, DidSaveTextDocumentParams, Position, Range,
                         TextDocumentContentChangeEvent)
from pygls.server import LanguageServer
from pygls.features import (COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                            TEXT_DOCUMENT_DID_OPEN, TEXT_DOCUMENT_DID_SAVE, WORKSPACE_EXECUTE_COMMAND)
from lark.tree import Tree
from lark.exceptions import (LexError, ParseError, UnexpectedCharacters,
                             UnexpectedInput, UnexpectedToken)
from lark import Lark, Token
from lark.parsers.lalr_puppet import ParserPuppet
from lark_patch import get_puppet, patch_parser
from dataclasses import dataclass
import logging
from copy import copy
from functools import lru_cache
from itertools import chain
from typing import Any, DefaultDict, Dict, List, Optional
from enum import Enum, auto
from collections import defaultdict
from annotation import chebi_search


# HACK patch the parser to product event hook
patch_parser()


# TODO remove this for production
logging.basicConfig(filename='pygls.log', filemode='w', level=logging.DEBUG)
RECURSION_LIMIT = 5  # Limit for flexible parsing
DUMMY_VALUE = '@DUMMY@'
LINE_CACHE_SIZE = 2048
N_MAX_RECOVERY = 20


'''=====Parsing-related Code===='''
dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, 'antimony.lark')) as r:
    parser_str = r.read()


@dataclass
class Species:
    stoich: str
    name: str


# TODO use transformer to keep state of whether a new "complete statement" was encountered
# remember to reset transformer every new call (or something)
# TODO add a TODO about writing own parser and custom recrusion loop


@dataclass
class Reaction:
    reactants: List[Species]
    products: List[Species]
    rate_law: str


@dataclass
class Assignment:
    name: str
    value: str


def walk_species_list(tree):
    ret = list()
    for species in tree.children:
        assert species.data == 'species'
        assert not isinstance(species, str)
        stoich = None
        name = None
        if len(species.children) == 1:
            stoich = '1'
            name = str(species.children[0])
        else:
            assert len(species.children) == 2
            stoich = str(species.children[0])
            name = str(species.children[1])

        assert name is not None
        ret.append(Species(stoich, name))

    return ret


class AntimonyError:
    def __init__(self, range_, message):
        self.range = range_
        self.message = message


class SemanticError(AntimonyError):
    def __init__(self, range_, message):
        super().__init__(range_, message)


class TypeError(SemanticError):
    def __init__(self, range_, message):
        super().__init__(range_, message)


# parses the whole file
whole_parser = Lark(parser_str, start='root', parser='lalr')


class SymbolType(Enum):
    UNKNOWN = 'Unknown'

    # Subtypes of UNKNOWN
    VARIABLE = 'Variable'
    SUBMODEL = 'Submodel'
    MODEL = 'Model'
    FUNCTION = 'Function'
    UNIT = 'Unit'

    # Subtype of VARIABLE. Also known as "formula"
    PARAMETER = 'Parameter'

    # Subtypes of PARAMETER
    SPECIES = 'Species'
    COMPARTMENT = 'Compartment'
    REACTION = 'Reaction'
    EVENT = 'Event'
    CONSTRAINT = 'Constraint'

    def __str__(self):
        return self.value

    def derives_from(self, other):
        if self == other:
            return True

        if other == SymbolType.UNKNOWN:
            return True

        if other == SymbolType.VARIABLE:
            return self in (SymbolType.SPECIES, SymbolType.COMPARTMENT, SymbolType.REACTION,
                            SymbolType.CONSTRAINT, SymbolType.CONSTRAINT)

        return False


class Variability(Enum):
    UNKNOWN = auto()
    CONSTANT = auto()
    VARIABLE = auto()


SymbolEntry = Dict[str, Any]


@dataclass
class NameItem:
    name: str
    name_range: Range
    const: bool  # const as specified by '$'
    const_range: Optional[Range] = None


@dataclass
class NameMaybeIn:
    name_item: NameItem
    comp_item: Optional[NameItem]


class SymbolTable:
    table: DefaultDict[str, SymbolEntry]

    def __init__(self):
        self.table = defaultdict(dict)

    def get_reactions(self):
        return {k: v for k, v in self.table.items() if v['type'] == SymbolType.REACTION}

    def update(self, name: str, data: SymbolEntry):
        assert 'type' not in data
        assert 'declared_type' not in data
        entry = self.table[name]
        entry.update(data)

    def update_type(self, name: str, stype: SymbolType, range_: Range, declared=False,
                    addl_data: Dict[str, Any] = dict()):
        '''Update the type of a symbol.

        Args:
            name:       The qualified name of the symbol.
            stype:      The new type of the symbol.
            range_:     The source range of this update, i.e. location in the text where this
                        update it type is inferred.
            declared:   Whether the typing was explicitly declared, i.e. in a declaration statement.
        '''
        entry = self.table[name]
        old_type = entry.get('type', SymbolType.UNKNOWN)
        if stype.derives_from(old_type):
            entry['type'] = stype
            entry['type_source'] = range_
        elif old_type.derives_from(stype):
            # legal, but useless information
            pass
        else:
            # TODO errored
            old_range: Range = entry['type_source']
            message = ("Type '{stype}' is incompatible with Type '{old_type}' indicated at line "
                       "{line}, column {column}").format(
                           stype=stype,
                           old_type=old_type,
                           line=old_range.start.line,
                           column=old_range.start.character,
            )
            error = TypeError(range_, message)
            return [error]

        if declared:
            old_declared_type = entry.get('declared_type', SymbolType.UNKNOWN)
            if stype.derives_from(old_declared_type):
                entry['decl_type'] = stype
                entry['decl_source'] = range_

        # Add the data
        self.update(name, addl_data)
        return []


# Holds information pertaining to one Antimony document
class Document:
    def __init__(self, text: str):
        self.table = SymbolTable()
        self.source = ''
        self.errors = list()
        self._parse(text)

    def get_errors(self):
        return self.errors

    def record_issues(self, issues):
        # TODO more sophisticated stuff? e.g. separate errors, warnings, syntax errors, semantic errors>
        self.errors += issues

    def _parse(self, text: str):
        text += '\n'
        # TODO more re-initializations
        self.species_names = set()

        root_puppet = get_puppet(whole_parser, 'root', text)
        # result = root_puppet.
        tree = self.recoverable_parse(root_puppet)
        assert tree is not None

        self.handle_parse_tree(tree)

    def recover_from_error(self, last_puppet, err_puppet):
        '''Given a puppet, return a copy of it with the lexer located at the next statement separator.

        All tokens between the current lexer position and the next statement separator are skipped.
        '''
        RECOVERY_TOKENS = ['SEMICOLON', '_ARROW', 'RPAR', 'NAME']
        old_lc = copy(last_puppet.lexer_state.state.line_ctr)

        # Try recovering
        # TODO have more criteria for skipping, e.g. if there is only one token and we have no
        # idea what it means
        # TODO probably want to copy line counter
        for i in range(N_MAX_RECOVERY):
            accepts = err_puppet.accepts()
            if '_STATEMENT_SEP' in accepts:
                err_puppet.feed_token(Token('_STATEMENT_SEP', DUMMY_VALUE))
                break

            for try_choice in RECOVERY_TOKENS:
                if try_choice in accepts:
                    err_puppet.feed_token(Token(try_choice, DUMMY_VALUE))
                    break
            else:
                # No choices
                err_puppet = copy(last_puppet)
                break
        else:
            # Could not recover error; give up parsing this line.
            err_puppet = copy(last_puppet)

        text = last_puppet.lexer_state.state.text
        try:
            next_pos = text.index(old_lc.newline_char, old_lc.char_pos) + 1
        except ValueError:
            try:
                next_pos = text.index(';', old_lc.char_pos) + 1
            except ValueError:
                next_pos = len(text)
        old_lc.feed(text[old_lc.char_pos: next_pos])
        # TODO update lexer_state.state.last_token
        err_puppet.lexer_state.state.line_ctr = old_lc
        return err_puppet

    def save_checkpoint(self, tree) -> bool:
        '''Returns whether we should save the state of the parser (i.e. in a ParserPuppet).

        Basically returns whether the rule that was just parsed is a complete rule, i.e. a statement
        or a model-end. This way, if we encounter an error later, we can restore the puppet to
        this complete state, find the next newline or semicolon, and continue parsing (having
        skipped the errored part).
        '''
        if tree.data in ('reaction', 'assignment', 'declaration', 'annotation', 'model'):
            return True

        return False

    def recoverable_parse(self, puppet):
        last_puppet = puppet.copy()
        while True:
            state = puppet.parser_state
            try:
                token = None
                for token in state.lexer.lex(state):
                    state.feed_token(token)
                    if (len(state.value_stack) > 1 and isinstance(state.value_stack[-2], Tree)):
                        if self.save_checkpoint(state.value_stack[-2]):
                            last_puppet = puppet.copy()

                token = Token.new_borrow_pos(
                    '$END', '', token) if token else Token('$END', '', 0, 1, 1)
                return state.feed_token(token, True)
            except (UnexpectedInput, UnexpectedCharacters) as e:
                # Encountered error; try to recover
                puppet = self.recover_from_error(last_puppet, puppet)
                last_puppet = puppet.copy()
            except Exception as e:
                # if self.debug:
                #     print("")
                #     print("STATE STACK DUMP")
                #     print("----------------")
                #     for i, s in enumerate(state.state_stack):
                #         print('%d)' % i , s)
                #     print("")
                raise

    def qname(self, scope, name):
        return scope + '/' + name

    def contains_dummy(self, tree):
        if isinstance(tree, Token):
            return tree.value == DUMMY_VALUE
        return self.contains_dummy(tree.children[-1])

    def get_range(self, left_token, right_token=None):
        assert isinstance(left_token, Token)
        assert right_token is None or isinstance(right_token, Token)
        if right_token is None:
            # return Range(left_token.line, left_token.column, left_token.end_line,
            #               left_token.end_column)
            return Range(Position(left_token.line - 1, left_token.column - 1),
                         Position(left_token.end_line - 1, left_token.end_column - 1))
        return Range(Position(left_token.line - 1, left_token.column - 1),
                     Position(right_token.end_line - 1, right_token.end_column - 1))

    def get_tree_range(self, tree):
        left = tree
        while not isinstance(left, Token):
            left = left.children[0]

        right = tree
        while not isinstance(right, Token):
            right = right.children[-1]

        return self.get_range(left, right)

    def handle_parse_tree(self, tree):
        scope = '_main'
        for child in tree.children:
            if child.data == 'reaction':
                self.handle_reaction(scope, child)
            elif child.data == 'assignment':
                self.handle_assignment(scope, child)
            elif child.data == 'declaration':
                self.handle_declaration(scope, child)

            self.species_names.discard(DUMMY_VALUE)

    def resolve_var_name(self, tree) -> NameItem:
        '''Resolve a var_name tree, i.e. one parsed from $A or A.
        '''
        name_token = tree.children[-1]
        if len(tree.children) == 1:
            return NameItem(str(name_token), self.get_range(name_token), False, None)

        var_range = self.get_range(tree.children[0])
        return NameItem(str(name_token), self.get_range(name_token), True, var_range)

    def resolve_name_maybe_in(self, tree) -> NameMaybeIn:
        assert len(tree.children) in (1, 2)

        name_item = self.resolve_var_name(tree.children[0])
        if len(tree.children) == 2:
            # TODO deal with comp variability
            comp_item = self.resolve_var_name(tree.children[1])
        else:
            assert len(tree.children) == 1
            comp_item = None

        return NameMaybeIn(name_item, comp_item)

    def handle_species_list(self, scope, tree):
        for species in tree.children:
            assert species.data == 'species'
            assert not isinstance(species, str)
            stoich = None
            var_name: Tree
            if len(species.children) == 1:
                stoich = '1'
                var_name = species.children[0]
            else:
                assert len(species.children) == 2
                stoich = str(species.children[0])
                var_name = species.children[1]

            name_token = var_name.children[-1]
            name = str(name_token)
            range_ = self.get_range(name_token)
            # TODO create a helper function that masks table.update_type and automatically add
            # the errors
            self.record_issues(
                self.table.update_type(self.qname(scope, name), SymbolType.SPECIES, range_)
            )

    def handle_formula(self, scope: str, tree: Tree):
        # TODO handle dummy tokens
        def pred(t):
            return isinstance(t, Token) and t.type == 'NAME' and t.value != DUMMY_VALUE
        for parameter in tree.scan_values(pred):
            name = str(parameter)
            range_ = self.get_range(parameter)
            self.record_issues(
                self.table.update_type(self.qname(scope, name), SymbolType.PARAMETER, range_)
            )

    def handle_reaction(self, scope, tree):
        if self.contains_dummy(tree):
            return

        reactants_index = 0
        reaction_name = None
        reaction_range = None

        if tree.children[0].data != 'reactants':
            name_mi = self.resolve_name_maybe_in(tree.children[0])
            reaction_name = name_mi.name_item.name
            reactants_index = 1
            reaction_range = name_mi.name_item.name_range
        else:
            # TODO generate a valid reaction name
            reaction_entries = self.table.get_reactions()
            anon_index = 0
            reaction_name = None
            while True:
                reaction_name = '_J{}'.format(anon_index)
                full_name = self.qname(scope, reaction_name)
                if full_name not in reaction_entries:
                    break
            reaction_range = self.get_tree_range(tree)

        assert reaction_name is not None
        self.handle_species_list(scope, tree.children[reactants_index])
        self.handle_species_list(scope, tree.children[reactants_index + 1])
        self.handle_formula(scope, tree.children[reactants_index + 2])

        # TODO get formatted reaction string and rate law string, and store them along with the
        # reaction
        self.record_issues(
            self.table.update_type(self.qname(scope, reaction_name), SymbolType.REACTION,
                                            reaction_range)
        )

    def handle_assignment(self, scope, tree):
        name = tree.children[0]
        value = tree.children[1]
        name_mi = self.resolve_name_maybe_in(name)
        self.record_issues(
            self.table.update_type(self.qname(scope, name_mi.name_item.name), SymbolType.PARAMETER,
                                   name_mi.name_item.name_range)
        )
        self.handle_formula(scope, value)

    def resolve_variab(self, tree) -> Variability:
        return {
            'var': Variability.VARIABLE,
            'const': Variability.CONSTANT,
        }[tree.data]

    def resolve_var_type(self, tree) -> SymbolType:
        return {
            'species': SymbolType.SPECIES,
            'compartment': SymbolType.COMPARTMENT,
            'formula': SymbolType.PARAMETER,
        }[tree.data]

    def handle_declaration(self, scope, tree):
        # TODO add modifiers in table
        modifiers = tree.children[0]
        variab = Variability.UNKNOWN
        stype = SymbolType.UNKNOWN
        if len(modifiers.children) == 1:
            mod = modifiers.children[0]
            if mod.data in ('const', 'var'):
                variab = self.resolve_variab(mod)
            else:
                stype = self.resolve_var_type(mod)
        elif len(modifiers.children) == 2:
            variab = self.resolve_variab(modifiers.children[0])
            stype = self.resolve_var_type(modifiers.children[1])

        for item in tree.children[1:]:
            name_mi = self.resolve_name_maybe_in(item.children[0])
            # TODO update variability
            self.record_issues(
                self.table.update_type(name_mi.name_item.name, stype, name_mi.name_item.name_range)
            )
            if len(item.children) == 2:
                # TODO add value in table
                value = item.children[1]

    def changed(self, change: TextDocumentContentChangeEvent, text: str):
        self.source = text
        # line_start = change.range.start
        # line_end = change.range.end
        # for line in range(line_start, line_end + 1):
        #     pass

        # TODO TODO TODO TODO IMPORTANT
        # For nonblocking command, use @json_server.thread().
        # See https://pygls.readthedocs.io/en/latest/pages/tutorial.html

    def completions(self, params: CompletionParams) -> CompletionList:
        return CompletionList(False, [
            CompletionItem(name) for name in self.species_names
        ])


'''=====Server-related Code===='''
server = LanguageServer()
# doc = Document()


def to_diagnostic(error: AntimonyError):
    return Diagnostic(
        range=error.range,
        message=error.message,
    )


def publish_diagnostics(uri: str):
    doc = server.workspace.get_document(uri)
    ant_doc = Document(doc.source)
    errors = ant_doc.errors
    diagnostics = [to_diagnostic(e) for e in errors]
    server.publish_diagnostics(uri, diagnostics)


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    publish_diagnostics(params.textDocument.uri)


count = 0


@server.feature(COMPLETION)
def completions(params: CompletionParams):
    text_doc = server.workspace.get_document(params.textDocument.uri)
    doc = Document(text_doc.source)
    return doc.completions(params)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    """Text document did open notification."""
    '''
    [Object(range=Object(start=Object(line=2, character=0), end=Object(line=2, character=1)), rangeLength=1, text='')
    '''
    # TODO don't need this
    publish_diagnostics(params.textDocument.uri)


@server.feature(TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls, params: DidSaveTextDocumentParams):
    """Text document did open notification."""
    publish_diagnostics(params.textDocument.uri)


@server.command('antimony.querySpecies')
def query_species(ls: LanguageServer, args):
    query = args[0]
    entities = chebi_search(query)
    results = [{
        'id': entity.chebiId,
        'name': entity.chebiAsciiName,
    } for entity in entities]
    return results


if __name__ == '__main__':
    server.start_io()
