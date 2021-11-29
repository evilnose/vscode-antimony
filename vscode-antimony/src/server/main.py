"""Temporary single-file server implementation.
Author: Gary Geng
"""
import os
import sys
import filecmp

EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(EXTENSION_ROOT, "pythonFiles", "lib", "python"))
sys.path.append(os.path.join(EXTENSION_ROOT, "server", "stibium"))

from stibium.api import AntCompletion, AntCompletionKind
from stibium.types import Issue, IssueSeverity

from bioservices_server.utils import AntFile, pygls_range, sb_position, get_antfile, sb_range
from bioservices_server.webservices import NetworkError, WebServices

import logging
from dataclasses import dataclass
from pygls.features import (CODE_LENS, COMPLETION, DEFINITION, HOVER, SIGNATURE_HELP, TEXT_DOCUMENT_DID_CHANGE,
                            TEXT_DOCUMENT_DID_OPEN, TEXT_DOCUMENT_DID_SAVE, WORKSPACE_EXECUTE_COMMAND)
from pygls.server import LanguageServer
from pygls.types import (CompletionItem, CompletionItemKind, CompletionList, CompletionParams, Diagnostic, DiagnosticSeverity,
                         DidChangeTextDocumentParams,
                         DidOpenTextDocumentParams, DidSaveTextDocumentParams, Hover, InsertTextFormat, Location, MarkupContent, MarkupKind,
                         TextDocumentContentChangeEvent, TextDocumentPositionParams)
import threading
import time


# TODO remove this for production
logging.basicConfig(filename='vscode-antimony.log', filemode='w', level=logging.DEBUG)

server = LanguageServer()
services = WebServices()

antfile_cache = None

#### Annotations ####
@server.command('antimony.getAnnotated')
def get_annotated(ls: LanguageServer, args):
    '''Return the list of annotated names as ranges'''
    text = args[0]
    antfile = AntFile('', text)
    qnames = antfile.analyzer.table.get_all_qnames()
    annotated = [q for q in qnames if antfile.get_annotations(q)]
    ranges = [pygls_range(a.name.range) for a in annotated]
    range_objs = [
        {
            'line': r.start.line,
            'column': r.start.character,
            'end_line': r.end.line,
            'end_column': r.end.character,
            } for r in ranges
    ]
    return range_objs

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
            'error': 'Connection Error!'
        }

#### Hover for displaying information ####
@server.feature(HOVER)
def hover(params: TextDocumentPositionParams):
    global antfile_cache
    if antfile_cache is None:
        text_doc = server.workspace.get_document(params.textDocument.uri)
        antfile_cache = get_antfile(text_doc)

    symbols, range_ = antfile_cache.symbols_at(sb_position(params.position))

    if not symbols:
        return None
    
    assert range_ is not None

    sym = symbols[0]
    text = sym.help_str()
    contents = MarkupContent(MarkupKind.Markdown, text)

    return Hover(
        contents=contents,
        range=pygls_range(range_),
    )

#### GOTO DEFINITION ####
@server.feature(DEFINITION)
def definition(params):
    global antfile_cache
    if antfile_cache is None:
        text_doc = server.workspace.get_document(params.textDocument.uri)
        antfile_cache = get_antfile(text_doc)
    srclocations, range_ = antfile_cache.goto(sb_position(params.position))
    definitions = [Location(
        loc.path,
        pygls_range(loc.range)) for loc in srclocations]
    # If no definitions, return None
    return definitions or None

#### helper and util ####
@server.thread()
@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    # re-generate parse tree
    global antfile_cache
    text_doc = server.workspace.get_document(params.textDocument.uri)
    antfile_cache = get_antfile(text_doc)


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls, params: DidSaveTextDocumentParams):
    pass


if __name__ == '__main__':
    server.start_io()