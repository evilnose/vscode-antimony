'''Monkey-patch Lark's implementation of the LALR Parser, as we need an "event hook" when reduce
is called.
'''
from lark.lexer import Token
from lark.tree import Tree
from lark.parsers.lalr_parser import ParserState, _Parser
from lark.parsers.lalr_puppet import ParserPuppet
from lark.parsers.lalr_analysis import Shift
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
    if tree.data == 'reaction':
        return True

    return False


def new_feed_token(self, token, is_end=False):
    state_stack = self.state_stack
    value_stack = self.value_stack
    states = self.parse_conf.states
    end_state = self.parse_conf.end_state
    callbacks = self.parse_conf.callbacks

    while True:
        state = state_stack[-1]
        try:
            action, arg = states[state][token.type]
        except KeyError:
            expected = {s for s in states[state].keys() if s.isupper()}
            raise UnexpectedToken(token, expected, state=self, puppet=None)

        assert arg != end_state

        if action is Shift:
            # shift once and return
            assert not is_end
            state_stack.append(arg)
            value_stack.append(token if token.type not in callbacks else callbacks[token.type](token))
            return
        else:
            # reduce+shift as many times as necessary
            rule = arg
            size = len(rule.expansion)
            if size:
                s = value_stack[-size:]
                del state_stack[-size:]
                del value_stack[-size:]
            else:
                s = []

            value = callbacks[rule](s)

            _action, new_state = states[state_stack[-1]][rule.origin.name]
            assert _action is Shift
            state_stack.append(new_state)
            value_stack.append(value)

            if is_end and state_stack[-1] == end_state:
                return value_stack[-1]


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
    ParserState.feed_token = new_feed_token
    _Parser.parse_from_state = new_parse_from_state
