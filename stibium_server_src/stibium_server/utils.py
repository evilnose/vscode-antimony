from pygls.workspace import Document
from stibium.api import AntCompletion, AntCompletionKind, AntFile, Completer
from stibium.analysis import AntTreeAnalyzer, get_qname_at_position

from stibium.parse import AntimonyParser
from stibium.utils import get_range, to_uri
from stibium.types import SrcLocation, SrcPosition, SrcRange

from pygls.types import CompletionItem, CompletionItemKind, CompletionList, CompletionParams, InsertTextFormat, Position, Range, TextDocumentPositionParams



def sb_position(position: Position):
    '''Converts pygls Position to stibium SrcPosition'''
    return SrcPosition(position.line + 1, position.character + 1)


def sb_range(range: Range):
    '''Converts pygls Position to stibium SrcPosition'''
    return SrcRange(range.start, range.end)


def pygls_position(srcpos: SrcPosition):
    return Position(srcpos.line - 1, srcpos.column - 1)


def pygls_range(srcrange: SrcRange):
    '''Converts pygls Position to stibium SrcPosition'''
    return Range(pygls_position(srcrange.start), pygls_position(srcrange.end))


def get_antfile(document: Document):
    return AntFile(document.path, document.source)
