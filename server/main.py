"""Temporary single-file server implementation."""

import os
import sys
EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(EXTENSION_ROOT, "pythonFiles", "lib", "python"))
import logging

from pygls.features import COMPLETION, TEXT_DOCUMENT_DID_OPEN
from pygls.server import LanguageServer
from pygls.types import CompletionItem, CompletionList, CompletionParams, DidOpenTextDocumentParams

from lark import Lark


logging.basicConfig(filename='pygls.log', filemode='w', level=logging.DEBUG)


'''=====Parsing-related Code===='''
parser = Lark(r'''
    reaction_list : reaction*
    reaction : reactants "->" products ";" rate_rule _NL
    reactants : species
        | species "+" reactants
    products : species
        | species "+" products
    species : name
        | NUMBER name
    rate_rule : "v"

    assignment_list : assignment*
    assignment : name "=" value _NL

    value : NUMBER
    name : (LETTER | "_") (LETTER | DIGIT | "_" )*

    root : reaction_list _NL assignment_list

    _NL: NEWLINE

    %import common.NUMBER
    %import common.DIGIT
    %import common.LETTER
    %import common.WS_INLINE
    %import common.NEWLINE
    %ignore WS_INLINE
        ''', start='root')


# Holds information pertaining to one Antimony document
class Document:
    def __init__(self):
        self.species = dict()
        self.parameters = dict()
        self.compartments = dict()

    def reparse(self, text: str):
        self.species = dict()
        self.parameters = dict()
        self.compartments = dict()

        text += '\n'
        # TODO handle exception here
        tree = parser.parse(text)
        return tree


'''=====Server-related Code===='''
server = LanguageServer()
doc = Document()

@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message("Text Document Did Open")
    ls.show_message_log("Validating Antimony...")

    # Get document from workspace
    text_doc = ls.workspace.get_document(params.textDocument.uri)
    # TODO can't parse this directly
    tree = doc.reparse(text_doc)

    # diagnostic = Diagnostic(
    #                  range=Range(Position(line-1, col-1), Position(line-1, col)),
    #                  message="Custom validation message",
    #                  source="Json Server"
    #              )

    # Send diagnostics
    # ls.publish_diagnostics(text_doc.uri, [diagnostic])

@server.feature(COMPLETION, trigger_characters=[','])
def completions(params: CompletionParams):
    """Returns completion items."""
    return CompletionList(False, [
        CompletionItem('"'),
        CompletionItem('['),
        CompletionItem(']'),
        CompletionItem('{'),
        CompletionItem('}')
    ])

# server.start_tcp('localhost', 8080)
server.start_io()
