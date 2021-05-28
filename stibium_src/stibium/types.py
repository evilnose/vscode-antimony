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

    def __repr__(self):
        return '{}:{}'.format(self.line, self.column)

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
    '''A range in text; uses 1-based index.
    
    Attributes:
        start: Start position of the range
        end: End position of the range. This is exclusive, meaning that this is one column after
             the last position in the range.
    '''
    start: SrcPosition
    end: SrcPosition

    def __repr__(self):
        return '{} - {}'.format(self.start, self.end)


@dataclass
class SrcLocation:
    '''Absolute location -- including a file path and a range.'''
    path: str  # absolute file path
    range: SrcRange


ASTNode = Union[Tree, Token]


class IssueSeverity(Enum):
    Error = auto()  # semantic error; guaranteed to fail if passed to Tellurium
    Warning = auto()
    # TODO more


class Issue:
    def __init__(self, range_: SrcRange, severity: IssueSeverity):
        self.range = range_
        self.message = ''
        self.severity = severity

    def __str__(self):
        return self.message

    def __repr__(self):
        return "{}({}, {}, '{}')".format(self.severity.name, type(self).__name__, self.range,
                                         self.message)


class IncompatibleType(Issue):
    def __init__(self, old_type, old_range, new_type, new_range):
        super().__init__(new_range, IssueSeverity.Error)
        self.old_type = old_type
        self.old_range = old_range
        self.new_type = new_type
        self.new_range = new_range
        self.message = ("Type '{new_type}' is incompatible with type '{old_type}' indicated on "
                        "line {old_line}:{old_column}").format(
            new_type=new_type,
            old_type=old_type,
            old_line=old_range.start.line,
            old_column=old_range.start.column,
        )


class ObscuredDeclaration(Issue):
    def __init__(self, old_range: SrcRange, new_range: SrcRange, name: str):
        super().__init__(old_range, IssueSeverity.Warning)
        self.old_range = old_range
        self.new_range = new_range
        self.name = name
        self.message = ("Declaration '{name}' is obscured by a declaration of the same name on "
                        "line {new_line}:{new_column}").format(
            name=name,
            new_line=new_range.start.line,
            new_column=new_range.start.column,
        )


class ObscuredValue(Issue):
    def __init__(self, old_range: SrcRange, new_range: SrcRange, name: str):
        super().__init__(old_range, IssueSeverity.Warning)
        self.old_range = old_range
        self.new_range = new_range
        self.name = name
        self.message = ("Value assignment to '{name}' is obscured by a later assignment on "
                        "line {new_line}:{new_column}").format(
            name=name,
            new_line=new_range.start.line,
            new_column=new_range.start.column,
        )


SyntaxError
class AntimonySyntaxError(Exception):
    # TODO this is far from complete. To include: filename, possible token choices,
    # and possibly even parser state?
    def __init__(self, text: str, pos: SrcPosition, end_pos: SrcPosition=None):
        message = f"unexpected token '{text}' at {pos}"
        super().__init__(message)
        self.text = text
        self.pos = pos
        self.end_pos = end_pos


class SymbolType(Enum):
    Unknown = 'unknown'

    # Subtypes of UNKNOWN
    Variable = 'variable'
    Submodel = 'submodel'
    Model = 'model'
    Function = 'function'
    Unit = 'unit'

    # Subtype of VARIABLE. Also known as "formula"
    Parameter = 'parameter'

    # Subtypes of PARAMETER
    Species = 'species'
    Compartment = 'compartment'
    Reaction = 'reaction'
    Event = 'event'
    Constraint = 'constraint'

    def __str__(self):
        return self.value

    def derives_from(self, other):
        if self == other:
            return True

        if other == SymbolType.Unknown:
            return True

        derives_from_param = self in (SymbolType.Species, SymbolType.Compartment,
                                      SymbolType.Reaction,
                                      SymbolType.Constraint)

        if other == SymbolType.Variable:
            return derives_from_param or self == SymbolType.Parameter

        if other == SymbolType.Parameter:
            return derives_from_param

        return False


class Variability(Enum):
    UNKNOWN = auto()
    CONSTANT = auto()
    VARIABLE = auto()
