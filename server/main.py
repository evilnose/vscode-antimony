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
from lark_patch import BreakRecursion, get_puppet, patch_parser


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


def resolve_unexpected_chars(e):
    '''Resolve an UnexpectedCharacters exception, so that parsing can resume

    In the case where the lexer encounters an unexpected character, i.e. one that is not defined by
    the grammar, we need to manually advance the pointer so that it is skipped.

    This needs to be done manually because we cannot afford the luxury of the `on_error` feature of
    `LALR_Parser`, which would have been able to handle this by itself:
    https://github.com/lark-parser/lark/blob/7ce0f7015fa24e83162afbdd129323f196273b97/lark/parsers/lalr_parser.py#L51
    
    '''
    s = e.puppet.lexer_state.state
    p = s.line_ctr.char_pos
    # feed the current token. Doesn't actually do anything but advance LineCounter.
    s.line_ctr.feed(s.text[p])


def try_parse(puppet):
    while True:
        puppet_copy = puppet.copy()
        try:
            s = puppet.lexer_state.state
            # HACK The latest release of lark has a bug that does not copy LineCounter
            lc = copy.copy(s.line_ctr)

            # Try parsing from this state
            result = try_parse_helper(puppet_copy, 0)
            if result is not None:
                return result

            # Parsing failed. Restore last valid parser state, skip this line, and keep trying.
            
            # Restore LineCounter copy
            puppet.lexer_state.state.line_ctr = lc
            
            # Skip this line. We can always find a newline because we manually append a newline
            # at the end of every text to be parsed.
            s = puppet.lexer_state.state
            nl_index = s.text.index(s.line_ctr.newline_char, s.line_ctr.char_pos)
            s.line_ctr.feed(s.text[s.line_ctr.char_pos : nl_index + 1])
        except BreakRecursion as e:
            # Update last valid state of puppet, and keep parsing from 0th-level recursion
            puppet = e.puppet


def try_parse_helper(puppet, level):
    while True:
        try:
            tree = puppet.resume_parse()
            return ParseResult(tree, level)
        except ParseError as e:
            # encountered parse error. Hand to next level
            return flexible_parse(e, level + 1)
        except UnexpectedCharacters as e:
            # resolve error and keep trying to parse
            resolve_unexpected_chars(e)


def flexible_parse(e, level):
    '''Try to parse even when there is an error'''
    if level > RECURSION_LIMIT:
        return None

    FAKE_TOKENS = { 'SEMICOLON', 'NAME', 'NUMBER', 'PLUS', 'RPAR' }

    # list of alternative possible parse results
    results = list()

    # try directly ignoring this token
    if e.token.type != '$END':
        results.append(try_parse_helper(e.puppet.copy(), level))

    # print(e.puppet.pretty())
    # TODO implement early stopping, i.e. stop early if the search depth exceeds the current
    # lowest depth
    # Also TODO determine a way to optimize the order of exploring choices.
    for choice, details in e.puppet.choices().items():
        if choice in FAKE_TOKENS:
            puppet = e.puppet.copy()
            puppet.feed_token(Token(choice, DUMMY_VALUE))

            if e.token in puppet.choices():
                puppet.feed_token(e.token)
                results.append(try_parse_helper(puppet, level))

    # filter out failed parses
    results = [r for r in results if r is not None]

    if len(results) == 0:
        # no successful parse under the recursion limit
        return None
    else:
        # return the result with the lowest level of recursion
        return min(results, key=lambda r: r.level)


# @lru_cache(maxsize=LINE_CACHE_SIZE)
# def cached_line_parse(line: str):
#     '''Basic cached parsing; likely useful for huge documents with quick inline modifications.'''
#     return line_parser.parse(line)


# Holds information pertaining to one Antimony document
class Document:
    def __init__(self):
        self.species = dict()
        self.parameters = dict()
        self.compartments = dict()
        self.species_names = set()
        self.source = ''

    def reparse(self, text: str):
        self.species_names = set()
        text += '\n'
        root_puppet = get_puppet(whole_parser, 'root', text)
        result = try_parse(root_puppet)
        if result is None:
            print('shoot')
            return
        tree = result.tree
        # try:
        #     tree = whole_parser.parse(text + '\n')
        # except (BreakRecursion, UnexpectedCharacters, ParseError) as e:
        #     puppet = getattr(e, 'puppet')
        #     result = try_parse(puppet)
        #     if result is None:
        #         # TODO skip this line
        #         print('shoot')
        #         return
        #     # TODO depend on the level and the number of original tokens, may choose to
        #     # discard tree after all, if too many tokens were extrapolated.
        #     tree = result.tree
        # except UnexpectedToken as e:
        #     server.show_message('Unexpected error while parsing: {}'.format(e))
        #     # TODO do something more here
        #     return

        print(tree)
        self.handle_parse_tree(tree)

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
