
from .types import ASTNode, SrcPosition, SrcRange

from lark.lexer import Token

import pathlib


def get_range(node: ASTNode):
    if isinstance(node, Token):
        return SrcRange(SrcPosition(node.line, node.column),
                     SrcPosition(node.end_line, node.end_column))
    else:
        return SrcRange(SrcPosition(node.meta.line, node.meta.column),
                     SrcPosition(node.meta.end_line, node.meta.end_column))


def tree_str(tree):
    if tree is None:
        return ''

    if isinstance(tree, Token):
        text = tree.value
        if tree.type == 'error_token':
            return text

        if (tree.type in ('NAME', 'NUMBER', 'END_MARKER', 'LPAR', 'RPAR', 'ESCAPED_STRING')
            or tree.value == '$'):
            return text
        elif tree.value in (',', ';', ':', 'const', 'var', 'species', 'formula', 'compartment'):
            return text + ' '

        return ' ' + text + ' '

    text = ''
    for child in tree.children:
        text += tree_str(child)

    return text


def to_uri(path: str) -> str:
    return pathlib.Path(path).as_uri()
