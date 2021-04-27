
from lark.lexer import Token
from classes import ASTNode
from pygls.types import Position, Range


def get_range(token: ASTNode):
    return Range(Position(token.line - 1, token.column - 1), # type: ignore
                 Position(token.end_line - 1, token.end_column - 1)) # type: ignore

def tree_str(self, tree):
    if tree is None:
        return ''

    if isinstance(tree, Token):
        text = tree.value
        if tree.type == 'error_token':
            return text

        if tree.type in ('NAME', 'NUMBER') or tree.value == '$':
            return text
        elif tree.value in (',', ';', ':', 'const', 'var'):
            return text + ' '

        return ' ' + text + ' '

    text = ''
    for child in tree.children:
        text += self.format(child)

    return text