
from typing import Optional
from stibium.ant_types import ErrorToken, LeafNode, Name, Newline, Number, Operator, SimpleStmt, StringLiteral, TreeNode, TrunkNode
from .types import ASTNode, SrcPosition, SrcRange

from lark.lexer import Token

import pathlib


def get_range(node: ASTNode):
    if isinstance(node, Token):
        return SrcRange(SrcPosition(node.line, node.column),
                        SrcPosition(node.end_line, node.end_column))
    else:
        if len(node.children) == 0:
            return SrcRange(SrcPosition(1, 1), SrcPosition(1, 1))

        return SrcRange(SrcPosition(node.meta.line, node.meta.column),
                        SrcPosition(node.meta.end_line, node.meta.end_column))


def formatted_code(node: Optional[TreeNode]):
    if node is None:
        return ''

    if isinstance(node, LeafNode):
        if isinstance(node, ErrorToken):
            return node.text

        prefix = ''
        suffix = ''
        if node.text in (',', ';', ':', 'const', 'var', 'species', 'formula', 'compartment'):
            suffix = ' '
        elif (isinstance(node, (Name, Number, StringLiteral, Newline))
              or node.text in ('(', ')', '$')):
            pass
        else:
            prefix = ' '
            suffix = ' '

        # Don't append space after semicolon if the next token is EOF, newline, or semicolon
        if node.text == ';' and (node.next is None or isinstance(node.next, Newline) or
                                 (isinstance(node.next, Operator) and node.next.text == ';')):
            suffix = ''

        return prefix + node.text + suffix

    assert isinstance(node, TrunkNode)
    text = ''
    for child in node.children:
        text += formatted_code(child)
    return text


def to_uri(path: str) -> str:
    return pathlib.Path(path).as_uri()
