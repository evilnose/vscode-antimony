from enum import Enum, auto
from typing import Union
from lark.lexer import Token

from lark.tree import Tree


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
        self.message = ("Type '{new_type}' is incompatible with Type '{old_type}' indicated at "
                        "{old_line}:{old_column}").format(
            new_type=new_type,
            old_type=old_type,
            old_line=old_range.start.line + 1,
            old_column=old_range.start.character + 1,
        )


class ObscuredDeclaration(AntWarning):
    def __init__(self, old_range, new_range, name):
        super().__init__(old_range)
        self.message = ("Declaration '{name}' is obscured by declaration of the same name at "
                        "{new_line}:{new_column}").format(
            name=name,
            new_line=new_range.start.line + 1,
            new_column=new_range.start.character + 1,
        )


class SymbolType(Enum):
    UNKNOWN = 'Unknown'

    # Subtypes of UNKNOWN
    VARIABLE = 'Variable'
    SUBMODEL = 'Submodel'
    MODEL = 'Model'
    FUNCTION = 'Function'
    UNIT = 'Unit'

    # Subtype of VARIABLE. Also known as "formula"
    PARAMETER = 'Parameter'

    # Subtypes of PARAMETER
    SPECIES = 'Species'
    COMPARTMENT = 'Compartment'
    REACTION = 'Reaction'
    EVENT = 'Event'
    CONSTRAINT = 'Constraint'

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
