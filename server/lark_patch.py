'''Monkey-patch Lark's implementation of the LALR Parser, as we need an "event hook" when reduce
is called.
'''
from lark.lark import Lark
from lark.lexer import Token
from lark.tree import Tree
from lark.parsers.lalr_parser import ParserState, _Parser, ParseConf
from lark.parsers.lalr_puppet import ParserPuppet
from lark.parsers.lalr_analysis import Shift
from lark.lexer import LexerThread
from lark.exceptions import UnexpectedToken, UnexpectedInput


class BreakRecursion(Exception):
    '''An exception to tell our code to break the search recursion.
    '''
    def __init__(self, puppet):
        super().__init__()
        self.puppet = puppet


def break_recursion(tree):
    '''Did finish reducing a rule. This raises an exception for certain rules, so that we can
    break out of the recursive search outside.
    '''
    if tree.data in ('reaction', 'assignment'):
        return True

    return False


def new_parse_from_state(self, state):
    # Main LALR-parser loop
    try:
        token = None
        for token in state.lexer.lex(state):
            state.feed_token(token)
            if (len(state.value_stack) > 1
                and isinstance(state.value_stack[-2], Tree)):
                if break_recursion(state.value_stack[-2]):
                    puppet = ParserPuppet(self, state, state.lexer)
                    raise BreakRecursion(puppet)

        token = Token.new_borrow_pos('$END', '', token) if token else Token('$END', '', 0, 1, 1)
        return state.feed_token(token, True)
    except UnexpectedInput as e:
        try:
            e.puppet = ParserPuppet(self, state, state.lexer)
        except NameError:
            pass
        raise e
    except Exception as e:
        if self.debug:
            print("")
            print("STATE STACK DUMP")
            print("----------------")
            for i, s in enumerate(state.state_stack):
                print('%d)' % i , s)
            print("")

        raise


def patch_parser():
    '''HACK Monkey-patch the Lark parser.'''
    _Parser.parse_from_state = new_parse_from_state


def get_puppet(lark_inst: Lark, start: str, text: str):
    '''HACK Generate a ParserPuppet without having encountered bugs.'''
    lalr_parser = lark_inst.parser.parser
    internal_parser = lalr_parser.parser
    lexer = lark_inst.parser.lexer
    lexer_thread = LexerThread(lexer, text)
    parse_conf = ParseConf(internal_parser.parse_table, internal_parser.callbacks, start)
    parser_state = ParserState(parse_conf, lexer_thread, None, None)
    return ParserPuppet(internal_parser, parser_state, parser_state.lexer)
