from pygls.workspace import Document
from stibium.ast import AntTreeAnalyzer

from stibium.parse import AntimonyParser
from stibium.utils import get_range, to_uri
from stibium.types import SrcLocation, SrcPosition, SrcRange

from pygls.types import CompletionItem, CompletionItemKind, CompletionList, CompletionParams, Position, Range, TextDocumentPositionParams



# Holds information pertaining to one Antimony document
# TODO move this to stibium.api
class AntFile:
    '''Interface for an Antimony source file and contains useful methods.'''
    def __init__(self, path: str, text: str):
        self.path = path
        self.text = text
        self.parser = AntimonyParser()
        self.tree = self.parser.parse(text)
        self.analyzer = AntTreeAnalyzer(self.tree)

    def symbols_at(self, position: SrcPosition):
        '''Return (symbols, range) where symbols is the list of symbols that the token at
        position may resolve to, and range is the range of the token under the position.

        TODO make a copy
        '''
        assert isinstance(position, SrcPosition)
        qname = self.analyzer.get_qname_at_position(position)
        if qname is None:
            return [], None
        return self.analyzer.resolve_qname(qname), get_range(qname.token)

    def goto(self, position: SrcPosition):
        symbols, range_ = self.symbols_at(position)
        if not symbols:
            return [], range_

        return [SrcLocation(
            to_uri(self.path),  # TODO might be other files when we add cross-file functionalities
            get_range(sym.def_token()),
        ) for sym in symbols], range_


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

    def completions(self, params: CompletionParams) -> CompletionList:
        # TODO more specific here
        return CompletionList(False, [
            CompletionItem(name, kind=CompletionItemKind.Text) for name in self.analyzer.get_all_names()
        ])



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
