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

# Temporary, before both packages are published
sys.path.append(os.path.join(EXTENSION_ROOT, "stibium_src"))
sys.path.append(os.path.join(EXTENSION_ROOT, "stibium_server_src"))

from stibium.types import AntError, AntWarning

from stibium_server.utils import AntFile, pygls_range, sb_position, get_antfile
from stibium_server.webservices import NetworkError, WebServices

from typing import List
import logging
from dataclasses import dataclass
from pygls.features import (COMPLETION, DEFINITION, HOVER, SIGNATURE_HELP, TEXT_DOCUMENT_DID_CHANGE,
                            TEXT_DOCUMENT_DID_OPEN, TEXT_DOCUMENT_DID_SAVE, WORKSPACE_EXECUTE_COMMAND)
from pygls.server import LanguageServer
from pygls.types import (CompletionItem, CompletionList, CompletionParams, Diagnostic, DiagnosticSeverity,
                         DidChangeTextDocumentParams,
                         DidOpenTextDocumentParams, DidSaveTextDocumentParams, Hover, Location, MarkupContent, MarkupKind,
                         TextDocumentContentChangeEvent, TextDocumentPositionParams)


# TODO remove this for production
logging.basicConfig(filename='bio-idek.log', filemode='w', level=logging.DEBUG)


'''=====Server-related Code===='''
server = LanguageServer()
services = WebServices()


def to_diagnostic(error: AntError):
    severity = DiagnosticSeverity.Error
    if isinstance(error, AntWarning):
        severity = DiagnosticSeverity.Warning

    return Diagnostic(
        range=pygls_range(error.range),
        message=error.message,
        severity=severity
    )


def publish_diagnostics(uri: str):
    doc = server.workspace.get_document(uri)
    antfile = get_antfile(doc)
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
    antfile = get_antfile(text_doc)
    # TODO better isolation; no pygls stuff in antfile
    return antfile.completions(params)


@server.feature(HOVER)
def hover(params: TextDocumentPositionParams):
    text_doc = server.workspace.get_document(params.textDocument.uri)
    antfile = get_antfile(text_doc)
    symbols, range_ = antfile.symbols_at(sb_position(params.position))
    if not symbols:
        return None

    assert range_ is not None

    # TODO fix the interface
    sym = symbols[0]
    contents = MarkupContent(MarkupKind.PlainText, sym.help_str())
    return Hover(
        contents=contents,
        range=pygls_range(range_),
    )


@server.feature(DEFINITION)
def definition(params):
    text_doc = server.workspace.get_document(params.textDocument.uri)
    antfile = get_antfile(text_doc)
    srclocations, range_ = antfile.goto(sb_position(params.position))

    definitions = [Location(
        loc.path,
        pygls_range(loc.range)) for loc in srclocations]
    # If no definitions, return None
    return definitions or None


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    """Text document did open notification."""
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
