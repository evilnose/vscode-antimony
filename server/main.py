"""Temporary single-file server implementation."""

import os
import sys
EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(EXTENSION_ROOT, "pythonFiles", "lib", "python"))

from pygls.features import COMPLETION, TEXT_DOCUMENT_DID_OPEN
from pygls.server import LanguageServer
from pygls.types import CompletionItem, CompletionList, CompletionParams, DidOpenTextDocumentParams

server = LanguageServer()

@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message("Text Document Did Open")
    ls.show_message_log("Validating Antimony...")

    # Get document from workspace
    text_doc = ls.workspace.get_document(params.textDocument.uri)

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
