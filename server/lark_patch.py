'''Monkey-patch Lark's implementation of the LALR Parser, as we need an "event hook" when reduce
is called.
'''
from copy import copy

from lark.lark import Lark
from lark.lexer import Token
from lark.tree import Tree
from lark.parsers.lalr_parser import ParserState, ParseConf
from lark.parsers.lalr_puppet import ParserPuppet
from lark.lexer import LexerThread, LineCounter
from lark.exceptions import UnexpectedToken, UnexpectedInput


def patch_parser():
    '''HACK Monkey-patch the Lark parser.'''
    # _Parser.parse_from_state = new_parse_from_state
    pass


def get_puppet(lark_inst: Lark, start: str, text: str):
    '''HACK Generate a ParserPuppet without having encountered bugs.'''
    lalr_parser = lark_inst.parser.parser
    internal_parser = lalr_parser.parser
    lexer = lark_inst.parser.lexer
    lexer_thread = LexerThread(lexer, text)
    parse_conf = ParseConf(internal_parser.parse_table, internal_parser.callbacks, start)
    parser_state = ParserState(parse_conf, lexer_thread, None, None)
    return ParserPuppet(internal_parser, parser_state, parser_state.lexer)
