from enum import Enum, auto
from typing import Union
from lark.lexer import Token

from lark.tree import Tree


ASTNode = Union[Tree, Token]
aaa = 1


class AntimonyError:
    def __init__(self, range_, message=None):
        self.range = range_
        self.message = message


class IncompatibleTypeError(AntimonyError):
    def __init__(self, old_type, old_range, new_type, new_range):
        super().__init__(new_range, None)
        self.message = ("Type '{new_type}' is incompatible with Type '{old_type}' indicated at line "
                        "{line}, column {column}").format(
            new_type=new_type,
            old_type=old_type,
            line=old_range.start.line + 1,
            column=old_range.start.character + 1,
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
