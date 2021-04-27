"""Temporary single-file server implementation.

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

from classes import AntError, AntWarning
from analysis import AntimonyTreeAnalyzer
from parse import AntimonyParser
from webservices import NetworkError, WebServices

from typing import List
import logging
from dataclasses import dataclass
from pygls.features import (COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                            TEXT_DOCUMENT_DID_OPEN, TEXT_DOCUMENT_DID_SAVE, WORKSPACE_EXECUTE_COMMAND)
from pygls.server import LanguageServer
from pygls.types import (CompletionItem, CompletionList, CompletionParams, Diagnostic, DiagnosticSeverity,
                         DidChangeTextDocumentParams,
                         DidOpenTextDocumentParams, DidSaveTextDocumentParams, Position, Range,
                         TextDocumentContentChangeEvent)


# TODO remove this for production
logging.basicConfig(filename='bio-idek.log', filemode='w', level=logging.DEBUG)


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


# Holds information pertaining to one Antimony document
class AntFile:
    '''Interface for an Antimony source file and contains useful methods.'''
    def __init__(self, text: str):
        self.source = ''
        self.parser = AntimonyParser()
        self.tree = self.parser.parse(text)
        self.analyzer = AntimonyTreeAnalyzer(self.tree)

    def get_errors(self):
        return self.analyzer.get_issues()

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

    def changed(self, change: TextDocumentContentChangeEvent, text: str):
        self.source = text
        # line_start = change.range.start
        # line_end = change.range.end
        # for line in range(line_start, line_end + 1):
        #     pass

    def completions(self, params: CompletionParams) -> CompletionList:
        # TODO
        return CompletionList(False, [
            CompletionItem(name) for name in self.analyzer.get_all_names()
        ])


'''=====Server-related Code===='''
server = LanguageServer()
services = WebServices()


def to_diagnostic(error: AntError):
    severity = DiagnosticSeverity.Error
    if isinstance(error, AntWarning):
        severity = DiagnosticSeverity.Warning

    return Diagnostic(
        range=error.range,
        message=error.message,
        severity=severity
    )


def publish_diagnostics(uri: str):
    doc = server.workspace.get_document(uri)
    antfile = AntFile(doc.source)
    errors = antfile.get_errors()
    diagnostics = [to_diagnostic(e) for e in errors]
    server.publish_diagnostics(uri, diagnostics)


@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    publish_diagnostics(params.textDocument.uri)


count = 0


@server.feature(COMPLETION)
def completions(params: CompletionParams):
    text_doc = server.workspace.get_document(params.textDocument.uri)
    antfile = AntFile(text_doc.source)
    return antfile.completions(params)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    """Text document did open notification."""
    '''
    [Object(range=Object(start=Object(line=2, character=0), end=Object(line=2, character=1)), rangeLength=1, text='')
    '''
    # TODO don't need this
    publish_diagnostics(params.textDocument.uri)


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls, params: DidSaveTextDocumentParams):
    """Text document did open notification."""
    publish_diagnostics(params.textDocument.uri)


@server.thread()
@server.command('antimony.sendQuery')
def query_species(ls: LanguageServer, args):
    try:
        database = args[0]
        query = args[1]
        if database == 'chebi':
            results = services.annot_search_chebi(query)
        elif database == 'uniprot':
            results = services.annot_search_uniprot(query)
        else:
            # This is not supposed to happen
            raise SystemError("Unknown database '{}'".format(database))

        return {
            'query': query,
            'items': results,
        }
    except NetworkError:
        return {
            'error': 'Connection Error'
        }


if __name__ == '__main__':
    server.start_io()
