
from stibium.types import ASTNode, SrcLocation, SrcPosition
from stibium.utils import get_range
from .lark_patch import get_puppet

import os

from lark.visitors import Visitor
from lark import Lark, Token
from lark.tree import Meta, Tree
from lark.exceptions import (LexError, ParseError, UnexpectedCharacters,
                             UnexpectedInput, UnexpectedToken)


def get_grammar_str():
    '''Load the grammar string.'''
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, 'antimony.lark')) as r:
        grammar_str = r.read()

    return grammar_str


class ParentVisitor(Visitor):
    '''Lark Visitor that creates parent pointers in the constructed tree'''
    def __default__(self, tree):
        for subtree in tree.children:
            if isinstance(subtree, Tree):
                assert not hasattr(subtree, 'parent')
                setattr(subtree, 'parent', tree)


class AntimonyParser:
    '''Frontend of a parser for Antimony, basically wrapping a Lark parser with error recovery.'''
    def __init__(self):
        grammar_str = get_grammar_str()
        self.parser = Lark(grammar_str, start='root', parser='lalr',
                                propagate_positions=True,
                                keep_all_tokens=True,
                                maybe_placeholders=True)

    def parse(self, text: str, recoverable=True, keep_parents: bool=True):
        '''Parse the tree, automatically appending a newline character to the end of the given text.
        
        TODO docs
        '''
        tree: Tree
        root_puppet = get_puppet(self.parser, 'root', text)
        tree = self._parse_with_puppet(root_puppet, recoverable)

        if keep_parents:
            tree = ParentVisitor().visit(tree)
        return tree

    def _parse_with_puppet(self, puppet, recoverable, token_callback = None):
        '''Parse with the given puppet in a recoverable way.
        '''
        if token_callback is None:
            token_callback = lambda _: None

        # HACK: this is to make error recovery behave normally in the case that there are
        # error tokens at the start of the text. In that case, the parser hasn't constructed a 
        # root node yet, so it is impossible to find the last "statement" node (from which to
        # construct an error node). In any case, this force-creates an empty statement in the tree
        # so that edge cases are avoided.
        # Two semicolons are fed because only after the second semicolon is fed, will the first
        # semicolon be parsed as an empty statement. Not sure why this is the case yet, but it
        # doesn't matter that much.
        if recoverable:
            INIT_TOKEN = Token('END_MARKER', '', 0, 0, 0, 0, 0, 0)  # type: ignore
            puppet.feed_token(INIT_TOKEN)
            puppet.feed_token(INIT_TOKEN)

        while True:
            try:
                # Main parser loop
                state = puppet.parser_state
                token = None
                for token in state.lexer.lex(state):
                    token_callback(token)
                    state.feed_token(token)

                # HACK feed an END_MARKER if there is no newline at the end of the file
                if token and token.type != 'END_MARKER' and 'END_MARKER' in puppet.choices():
                    line_ctr = state.lexer.state.line_ctr
                    state.feed_token(Token('END_MARKER', '', line_ctr.char_pos, line_ctr.line,
                                     line_ctr.column, line_ctr.line,
                                     line_ctr.column, line_ctr.char_pos))  # type: ignore

                token = Token.new_borrow_pos(
                    '$END', '', token) if token else Token('$END', '', 0, 1, 1)  # type: ignore
                token_callback(token)

                tree = state.feed_token(token, True)

                # remove the dummy tokens
                if recoverable:
                    tree.children = tree.children[2:]

                return tree
            except UnexpectedCharacters as e:
                if recoverable:
                    self._recover_from_error(puppet, token_callback)
                else:
                    raise e
            except UnexpectedInput as e:
                if recoverable:
                    self._recover_from_error(puppet, token_callback, getattr(e, 'token'))
                else:
                    raise e

    def _recover_from_error(self, err_puppet, token_callback, token=None):
        '''Given a puppet in error, restore the puppet to a state from which it can keep parsing.

        Error tokens or error nodes may be created.
        '''
        def last_statement(state_stack, states):
            until_index = None
            for until_index, state_arg in reversed(list(enumerate(state_stack))):
                if 'statement' in states[state_arg]:
                    break
            return until_index

        def update_stacks(value_stack, state_stack, start_index):
            all_nodes = value_stack[start_index-1:]

            if all_nodes:
                meta = Meta()
                meta.line = all_nodes[0].line
                meta.column = all_nodes[0].column
                meta.end_line = all_nodes[-1].end_line
                meta.end_column = all_nodes[-1].end_column
                meta.empty = False
                node = Tree('error_node', all_nodes, meta=meta)
                # propgate positions
                value_stack[start_index - 2].children.append(node)
                del state_stack[start_index:]
                del value_stack[start_index-1:]

                return True

            return False

        pstate = err_puppet.parser_state
        until_index = last_statement(pstate.state_stack, pstate.parse_conf.states)

        if token:
            token_callback(token)

        # make all nodes until the last statement to be the children of an error node
        if update_stacks(pstate.value_stack, pstate.state_stack, until_index + 1):
            # Retrace steps to feed this token again
            if token:
                s = err_puppet.lexer_state.state
                s.line_ctr.column = token.column
                s.line_ctr.line = token.line
                s.line_ctr.char_pos = token.pos_in_stream
        else:
            # No error node created; create token instead
            if token:
                token.type = 'error_token'
                pstate.value_stack[-1].children.append(token)
                return

            s = err_puppet.lexer_state.state
            p = s.line_ctr.char_pos
            line = s.line_ctr.line
            col = s.line_ctr.column
            text = s.text[p]
            assert text != s.line_ctr.newline_char
            tok = Token('error_token', text, p, line, col, line, col + 1) # type: ignore
            token_callback(tok)
            pstate.value_stack[-1].children.append(tok)
            s.line_ctr.feed('?')
    
    def get_state_at_position(self, text: str, stop_pos: SrcPosition):
        '''Get the parser state & value stacks at the given position.
        TODO see note in Completer.__init__(). Possibly to get the leaf and get the previous token
        '''

        class PositionReached(Exception):
            pass

        def token_callback(token: Token):
            '''
            In those cases, stop (^ indicates lexer position, * indicates stop position)

            1) last_token      token
                         ^       *
            2) last_token      token
                         ^  *
            '''
            if token.type == '$END':
                raise PositionReached
            token_range = get_range(token)
            if stop_pos <= token_range.end:
                raise PositionReached

        # TODO OPTIMIZE: instead of re-parsing the entire text, try picking out only the
        # relevant lines nearby, and then parse only that.
        # that's why we want the leaf
        puppet = get_puppet(self.parser, 'root', text)
        try:
            self._parse_with_puppet(puppet, True, token_callback)
        except PositionReached:
            return puppet.parser_state
        
        return puppet.parser_state

