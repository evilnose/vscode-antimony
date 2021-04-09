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

TODO URGENT: Either Monkey-patch Parser or modify the grammar to do things line by line. If
monkey-patch and can't parse something, advance the lexer to a newline and keep going.

TODO new approach to error tolerance: chill out. If an error is encountered, then stop, restore
the last valid state (i.e. at the end of a statement), find the next newline or semicolon, skip
to there, and parse. (be careful here. what about models?)
NOTE: still probably need dummy tokens, and a way to preserve the context
short-term TODO list
* definition
* display syntax error
* uniprot
* syntax highlighting?

NOTE: idea for optimization: for whatever change made in a range, only re-parse items in that range.
But if the change crosses model boundaries, need to extend the changed range to encompass the model
as well. Should be a good enough optimization for now.
"""

import os
import sys
import logging
import copy
from functools import lru_cache
from itertools import chain
from typing import List

EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(EXTENSION_ROOT, "pythonFiles", "lib", "python"))

from dataclasses import dataclass

from lark import Lark, Token
from lark.exceptions import (LexError, ParseError, UnexpectedCharacters,
                             UnexpectedInput, UnexpectedToken)
from lark.tree import Tree
from pygls.features import (COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                            TEXT_DOCUMENT_DID_OPEN, TEXT_DOCUMENT_DID_SAVE, WORKSPACE_EXECUTE_COMMAND)
from pygls.server import LanguageServer
from pygls.types import (CompletionItem, CompletionList, CompletionParams,
                         DidChangeTextDocumentParams,
                         DidOpenTextDocumentParams, DidSaveTextDocumentParams, ExecuteCommandParams,
                         TextDocumentContentChangeEvent)
from annotation import chebi_search
from lark_patch import get_puppet, patch_parser
from lark.parsers.lalr_puppet import ParserPuppet


# HACK patch the parser to product event hook
patch_parser()


# TODO remove this for production
logging.basicConfig(filename='pygls.log', filemode='w', level=logging.DEBUG)
RECURSION_LIMIT = 5  # Limit for flexible parsing
DUMMY_VALUE = '@@DUMMY@@'
LINE_CACHE_SIZE = 2048


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


# parses the whole file
whole_parser = Lark(parser_str, start='root', parser='lalr')
# line_parser = Lark(parser_str, start='line', parser='lalr')

@dataclass
class ParseResult:
    tree: Tree
    level: int


# Holds information pertaining to one Antimony document
class Document:
    def __init__(self):
        self.species = dict()
        self.parameters = dict()
        self.compartments = dict()
        self.species_names = set()
        self.source = ''
        self.dirty = False

    def reparse(self, text: str):
        text += '\n'
        # TODO more re-initializations
        self.species_names = set()

        root_puppet = get_puppet(whole_parser, 'root', text)
            # result = root_puppet.
        tree = self.recoverable_parse(root_puppet)
        assert tree is not None

        self.handle_parse_tree(tree)

    def find_separator(self, puppet):
        '''Given a puppet, return a copy of it with the lexer located at the next statement separator.

        All tokens between the current lexer position and the next statement separator are skipped.
        '''
        puppet = puppet.copy()
        while True:
            try:
                state = puppet.parser_state
                for token in state.lexer.lex(state):
                    if token.type == 'STATEMENT_SEP':
                        return puppet
                return puppet
            except UnexpectedCharacters:
                pass

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

                token = Token.new_borrow_pos('$END', '', token) if token else Token('$END', '', 0, 1, 1)
                return state.feed_token(token, True)
            except (UnexpectedInput, UnexpectedCharacters) as e:
                # Encountered error; skip parsing to next semicolon or newline
                puppet = self.find_separator(last_puppet)
            except Exception as e:
                # if self.debug:
                #     print("")
                #     print("STATE STACK DUMP")
                #     print("----------------")
                #     for i, s in enumerate(state.state_stack):
                #         print('%d)' % i , s)
                #     print("")

                raise

    def handle_parse_tree(self, tree):
        for child in tree.children:
            if child.data == 'reaction':
                self.handle_reaction_node(child)

            elif child.data == 'assignment':
                self.handle_assignment_node(child)
            
            self.species_names.discard(DUMMY_VALUE)

    def handle_reaction_node(self, tree):
        reactants_index = 0
        reaction_name = None

        if isinstance(tree.children[0], Token):
            reaction_name = str(tree.children[0])
            reactants_index = 1

        reactants = walk_species_list(tree.children[reactants_index])
        products = walk_species_list(tree.children[reactants_index + 1])
        rate_law = tree.children[reactants_index + 2]  # this is a mathematical expresion
        assert isinstance(rate_law, Tree)

        for species in chain(reactants, products):
            self.species_names.add(species.name)

        # Add the names of all the variables
        for species in rate_law.find_data('var'):
            # TODO better way to do this: first add species names etc. from reactions and
            # assignments. After that, add unknown variables from these equations that
            # are not species or parameters or what not, and label them as unknown.
            self.species_names.add(str(species.children[0]))

    def handle_assignment_node(self, tree):
        assert isinstance(tree.children[0], Token)
        assert isinstance(tree.children[1], Token)
        name = str(tree.children[0])
        value = str(tree.children[1])
        self.species_names.add(name)

    def changed(self, change: TextDocumentContentChangeEvent, text: str):
        self.dirty = True
        self.source = text
        # line_start = change.range.start
        # line_end = change.range.end
        # for line in range(line_start, line_end + 1):
        #     pass

    def completions(self, params: CompletionParams) -> CompletionList:
        if self.dirty:
            self.reparse(self.source)
            self.dirty = False
        return CompletionList(False, [
            CompletionItem(name) for name in self.species_names
        ])


'''=====Server-related Code===='''
server = LanguageServer()
doc = Document()


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    doc.reparse(params.textDocument.text)


@server.feature(COMPLETION)
def completions(params: CompletionParams):
    return doc.completions(params)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    """Text document did open notification."""
    '''
    [Object(range=Object(start=Object(line=2, character=0), end=Object(line=2, character=1)), rangeLength=1, text='')
    '''
    text_doc = ls.workspace.get_document(params.textDocument.uri)
    # ls.show_message(repr(params.contentChanges))
    for change in params.contentChanges:
        change: TextDocumentContentChangeEvent
        doc.changed(change, text_doc.source)


@server.feature(TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls, params: DidSaveTextDocumentParams):
    """Text document did open notification."""
    pass


@server.command('antimony.querySpecies')
def query_species(ls: LanguageServer, args):
    query = args[0]
    entities = chebi_search(query)
    results = [ {
        'id': entity.chebiId,
        'name': entity.chebiAsciiName,
    } for entity in entities]
    return results


if __name__ == '__main__':
    server.start_io()
