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
"""

import os
import sys

EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(EXTENSION_ROOT, "pythonFiles", "lib", "python"))
import logging

from pygls.features import COMPLETION, TEXT_DOCUMENT_DID_CHANGE, TEXT_DOCUMENT_DID_OPEN, TEXT_DOCUMENT_DID_SAVE
from pygls.server import LanguageServer
from pygls.types import CompletionItem, CompletionList, CompletionParams, DidChangeTextDocumentParams, DidOpenTextDocumentParams, DidSaveTextDocumentParams, TextDocumentContentChangeEvent

from dataclasses import dataclass
from typing import List
from itertools import chain
from lark.exceptions import LexError, ParseError, UnexpectedCharacters, UnexpectedInput
from lark import Lark, Token
from lark.tree import Tree


logging.basicConfig(filename='pygls.log', filemode='w', level=logging.DEBUG)
RECURSION_LIMIT = 5  # Limit for flexible parsing
DUMMY_VALUE = '@@DUMMY@@'


'''=====Parsing-related Code===='''
PARSER_STR = r'''
    reaction_list : reaction*
    reaction : [NAME ":"] reactants "->" products ";" rate_law [";"]
    reactants : species ("+" species)*
    products : species ("+" species)*
    species : [NUMBER] NAME
    ?rate_law : sum

    assignment_list : assignment*
    assignment : NAME "=" value

    ?value : NUMBER

    ?line: reaction
        | assignment

    ?sum : product
        | sum "+" product           -> add
        | sum "-" product           -> sub

    ?product : exponential
        | product "*" exponential   -> mul
        | product "/" exponential   -> div

    ?exponential: atom
        | exponential "^" atom      -> exp
    
    ?atom : NUMBER                  -> number
        | NAME                      -> var
        | "-" atom                  -> neg
        | "(" sum ")"

    root : (line _NL)*

    _NL: NEWLINE

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.DIGIT
    %import common.LETTER
    %import common.WS_INLINE
    %import common.NEWLINE
    %ignore WS_INLINE
'''


@dataclass
class Species:
    stoich: str
    name: str


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
whole_parser = Lark(PARSER_STR, start='root', parser='lalr')
line_parser = Lark(PARSER_STR, start='line', parser='lalr')


@dataclass
class ParseResult:
    tree: Tree
    level: int


def resolve_unexpected_chars(e):
    '''Resolve an UnexpectedCharacters exception, so that parsing can resuming

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


def try_parse(puppet, level):
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
        results.append(try_parse(e.puppet.copy(), level))

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
                results.append(try_parse(puppet, level))

    # filter out failed parses
    results = [r for r in results if r is not None]

    if len(results) == 0:
        # no successful parse under the recursion limit
        return None
    else:
        # return the result with the lowest level of recursion
        return min(results, key=lambda r: r.level)


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
        lines = text.splitlines()
        for row, line in enumerate(lines):
            line = line.strip()
            if len(line) == 0:
                continue
            try:
                tree = line_parser.parse(line)
            except UnexpectedCharacters as e:
                resolve_unexpected_chars(e)
                # dynamic property; do this to avoid upsetting the IDE
                puppet = getattr(e, 'puppet')
                result = try_parse(puppet, 0)
                if result is None: continue  # failed to parse
                tree = result.tree
            except UnexpectedInput as e:
                server.show_message('Error UnexpectedInput: {}'.format(e))
                continue
            except ParseError as e:
                result = flexible_parse(e, 0)
                if result is None: continue  # failed to parse

                # TODO depend on the level and the number of original tokens, may choose to
                # discard tree after all, if too many tokens were extrapolated.
                tree = result.tree

            if tree.data == 'reaction':
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

            elif tree.data == 'assignment':
                assert isinstance(tree.children[0], Token)
                assert isinstance(tree.children[1], Token)
                name = str(tree.children[0])
                value = str(tree.children[1])
                self.species_names.add(name)
            
            self.species_names.discard(DUMMY_VALUE)

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

if __name__ == '__main__':
    server.start_io()
