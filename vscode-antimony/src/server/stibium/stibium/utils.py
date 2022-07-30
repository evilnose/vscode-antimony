
import os
from typing import Optional

from lark.tree import Tree
from stibium.ant_types import Atom, ErrorToken, LeafNode, Name, Newline, Number, Operator, SimpleStmt, StringLiteral, TreeNode, TrunkNode
from .types import ASTNode, SrcPosition, SrcRange

from lark.lexer import Token

import pathlib


def get_abs_path(filename: str):
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filename)


def get_token_range(token: Token):
    return SrcRange(SrcPosition(token.line, token.column),
                    SrcPosition(token.end_line, token.end_column))

def get_tree_range(tree: Tree):
    return SrcRange(SrcPosition(tree.meta.line, tree.meta.column),
                    SrcPosition(tree.meta.end_line, tree.meta.end_column))


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
              or node.text in ('(', ')', '$') or
              (isinstance(node.parent, Atom) and isinstance(node, Operator))):
            # TODO in the case where we have -atom or +atom, we might not want to change the spacing
            # since the user might have something weird like + + - - + 3
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
