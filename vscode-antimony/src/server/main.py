"""Temporary single-file server implementation.
Author: Gary Geng
"""
import os
import sys


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


'''=====Server-related Code===='''
server = LanguageServer()
services = WebServices()


def to_diagnostic(issue: Issue):
    '''Convert the Stibium Issue object to a pygls Diagnostic object'''
    severity = DiagnosticSeverity.Error
    if issue.severity == IssueSeverity.Warning:
        severity = DiagnosticSeverity.Warning

    return Diagnostic(
        range=pygls_range(issue.range),
        message=issue.message,
        severity=severity
    )


def _publish_diagnostics(uri: str) -> AntFile:
    doc = server.workspace.get_document(uri)
    antfile = get_antfile(doc)
    errors = antfile.get_issues()
    diagnostics = [to_diagnostic(e) for e in errors]
    server.publish_diagnostics(uri, diagnostics)
    return antfile


@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    antfile = _publish_diagnostics(params.textDocument.uri)


@server.feature(COMPLETION)
def completions(params: CompletionParams):
    text_doc = server.workspace.get_document(params.textDocument.uri)
    antfile = get_antfile(text_doc)
    # TODO better isolation; no pygls stuff in antfile
    ant_completions = antfile.completions(sb_position(params.position))

    # TODO move this function to utils
    def map_completion(ant_compl: AntCompletion):
        if ant_compl.kind == AntCompletionKind.TEXT:
            return CompletionItem(ant_compl.text, kind=CompletionItemKind.Text)
        elif ant_compl.kind == AntCompletionKind.RATE_LAW:
            return CompletionItem('(mass action) ' + ant_compl.text, kind=CompletionItemKind.Text,
                                  insert_text=ant_compl.text,
                                  insert_text_format=InsertTextFormat.Snippet)
        else:
            assert False, 'Not implemented'

    items = list(map(map_completion, ant_completions))
    return CompletionList(False, items)


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
    text = sym.help_str()
    contents = MarkupContent(MarkupKind.Markdown, text)
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


# Performance trick: don't re-parse as soon as DidChange is issued, but wait for 0.5 seconds. If
# the user makes any more changes within that 0.5 seconds, don't actually perform the work.
lock = threading.Lock()
latest_millis = 0

@server.thread()
@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    """Text document did open notification."""
    global latest_millis

    def callback(millis):
        with lock:
            if millis < latest_millis:
                return
            assert millis == latest_millis
        _publish_diagnostics(params.textDocument.uri)

    cur_millis = int(time.time() * 1000)

    with lock:
        latest_millis = max(cur_millis, latest_millis)

    t = threading.Timer(0.5, lambda: callback(cur_millis))
    t.start()


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls, params: DidSaveTextDocumentParams):
    """Text document did open notification."""
    antfile = _publish_diagnostics(params.textDocument.uri)


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


if __name__ == '__main__':
    server.start_io()