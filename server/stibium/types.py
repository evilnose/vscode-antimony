from dataclasses import dataclass
from enum import Enum, auto
from typing import Union

from lark.lexer import Token
from lark.tree import Tree


@dataclass(eq=True)
class SrcPosition:
    '''A position in text; uses 1-based index.'''
    line: int
    column: int

    def __ge__(self, other):
        if self.line > other.line:
            return True
        if self.line == other.line:
            return self.column >= other.column
        return False

    def __gt__(self, other):
        if self.line > other.line:
            return True
        if self.line == other.line:
            return self.column > other.column
        return False

    def __le__(self, other):
        if self.line < other.line:
            return True
        if self.line == other.line:
            return self.column <= other.column
        return False

    def __lt__(self, other):
        if self.line < other.line:
            return True
        if self.line == other.line:
            return self.column < other.column
        return False
        

@dataclass
class SrcRange:
    '''A position in text; uses 0-based index.'''
    start: SrcPosition
    end: SrcPosition


@dataclass
class SrcLocation:
    '''Absolute location -- including a file path and a range.'''
    path: str  # absolute file path
    range: SrcRange


ASTNode = Union[Tree, Token]


class AntError:
    def __init__(self, range_):
        self.range = range_
        self.message = ''

    def __str__(self):
        return self.message

    def __repr__(self):
        return "{}('{}', '{}')".format(type(self).__name__, self.range, self.message)


class AntWarning(AntError):
    pass


class IncompatibleType(AntError):
    def __init__(self, old_type, old_range, new_type, new_range):
        super().__init__(new_range)
        self.message = ("Type '{new_type}' is incompatible with type '{old_type}' indicated on "
                        "line {old_line}:{old_column}").format(
            new_type=new_type,
            old_type=old_type,
            old_line=old_range.start.line,
            old_column=old_range.start.column,
        )


class ObscuredDeclaration(AntWarning):
    def __init__(self, old_range, new_range, name):
        super().__init__(old_range)
        self.message = ("Declaration '{name}' is obscured by a declaration of the same name on "
                        "line {new_line}:{new_column}").format(
            name=name,
            new_line=new_range.start.line,
            new_column=new_range.start.column,
        )


class ObscuredValue(AntWarning):
    def __init__(self, old_range, new_range, name):
        super().__init__(old_range)
        self.message = ("Value assignment to '{name}' is obscured by a later assignment on "
                        "line {new_line}:{new_column}").format(
            name=name,
            new_line=new_range.start.line,
            new_column=new_range.start.column,
        )


class SymbolType(Enum):
    UNKNOWN = 'unknown'

    # Subtypes of UNKNOWN
    VARIABLE = 'variable'
    SUBMODEL = 'submodel'
    MODEL = 'model'
    FUNCTION = 'function'
    UNIT = 'unit'

    # Subtype of VARIABLE. Also known as "formula"
    PARAMETER = 'parameter'

    # Subtypes of PARAMETER
    SPECIES = 'species'
    COMPARTMENT = 'compartment'
    REACTION = 'reaction'
    EVENT = 'event'
    CONSTRAINT = 'constraint'

    def __str__(self):
        return self.value

    def derives_from(self, other):
        if self == other:
            return True

        if other == SymbolType.UNKNOWN:
            return True

        derives_from_param = self in (SymbolType.SPECIES, SymbolType.COMPARTMENT,
                                      SymbolType.REACTION,
                                      SymbolType.CONSTRAINT)

        if other == SymbolType.VARIABLE:
            return derives_from_param or self == SymbolType.PARAMETER

        if other == SymbolType.PARAMETER:
            return derives_from_param

        return False


class Variability(Enum):
    UNKNOWN = auto()
    CONSTANT = auto()
    VARIABLE = auto()
