
from classes import ASTNode
from pygls.types import Position, Range


def get_range(token: ASTNode):
    return Range(Position(token.line - 1, token.column - 1), # type: ignore
                 Position(token.end_line - 1, token.end_column - 1)) # type: ignore
