

# Helper classes to hold name structures
from dataclasses import dataclass
from typing import List, Optional, cast

from lark.lexer import Token
from lark.tree import Tree

from stibium.types import SrcRange, SymbolType, Variability


@dataclass
class NameItem:
    const_tok: Optional[Token]
    name_tok: Token


@dataclass
class NameMaybeIn:
    name_item: NameItem
    comp_item: Optional[NameItem]


class TreeNode:
    parent: Optional['TrunkNode']
    range: SrcRange

    def __init__(self, parent: Optional['TrunkNode'], range_: SrcRange):
        self.parent = parent
        self.range = range_

    def check_rep(self):
        pass


class TrunkNode(TreeNode):
    children: List['TreeNode']

    def __init__(self, parent: Optional['TrunkNode'], children: List[TreeNode], range_: SrcRange):
        super().__init__(parent, range_)
        self.children = children
        self.check_rep()


class LeafNode(TreeNode):
    text: str

    def __init__(self, parent: Optional['TrunkNode'], text: str, range_: SrcRange):
        super().__init__(parent, range_)
        self.text = text
        self.check_rep()


class ArithmeticExpr(TreeNode):
    '''Base class for arithmetic expressions.'''
    pass


class Sum(ArithmeticExpr, TrunkNode):
    '''Arithmetic expression with an addition/subtraction root operator.'''
    pass


class Product(ArithmeticExpr, TrunkNode):
    '''Arithmetic expression with a multiplication/division root operator.'''
    pass


class Power(ArithmeticExpr, TrunkNode):
    '''Arithmetic expression with a power root operator.'''
    pass


class Atom(ArithmeticExpr):
    '''Atomic arithmetic expression.'''
    pass


class Name(LeafNode):
    def check_rep(self):
        assert bool(self.text)


class Number(ArithmeticExpr, LeafNode):
    def get_value(self):
        return float(self.text)
    
    def check_rep(self):
        self.get_value()


class Operator(LeafNode):
    def __init__(self, parent: Optional['TrunkNode'], text: str, type_: str, range_: SrcRange):
        super().__init__(parent, text, range_)
        self.type = type_


class Keyword(LeafNode):
    pass


class VarName(TrunkNode):
    def is_const(self):
        return self.children[0] is not None

    def get_name(self):
        return str(self.children[1])

    def check_rep(self):
        assert len(self.children) == 2
        assert self.children[0] is None or isinstance(self.children[0], LeafNode)
        assert isinstance(self.children[1], Name)
    

class InComp(TrunkNode):
    def get_comp(self) -> VarName:
        return cast(VarName, self.children[1])

    def check_rep(self):
        assert len(self.children) == 2
        assert isinstance(self.children[0], LeafNode) and self.children[0].text == 'in'
        assert isinstance(self.children[1], VarName)


class MaybeIn(TrunkNode):
    def get_var_name(self):
        return cast(VarName, self.children[0])
    
    def is_in_comp(self):
        return self.children[1] is not None

    def get_comp(self):
        return cast(InComp, self.children[1]).get_comp()
    
    def check_rep(self):
        assert len(self.children) == 2
        assert isinstance(self.children[0], VarName)
        assert self.children[1] is None or isinstance(self.children[1], InComp)


# # TODO move this to another class, e.g. logical/model types
# # TODO create new classes Name and Node to replace Token and Tree
# @dataclass
# class Species:
#     stoich: float
#     name: Token


class Species(TrunkNode):
    def get_stoich(self):
        if self.children[0] is None:
            return 1

        return cast(Number, self.children[0]).get_value()

    def get_var_name(self):
        return cast(VarName, self.children[1])

    def get_name(self):
        return self.get_var_name().get_name()

    def check_rep(self):
        assert len(self.children) == 2
        assert self.children[0] is None or isinstance(self.children[0], Number)
        assert isinstance(self.children[1], VarName)


class ReactionName(TrunkNode):
    '''Represents the 'J0:' at the start of the reaction.'''
    def get_maybein(self):
        return cast(MaybeIn, self.children[0])

    def get_name(self):
        return self.get_maybein().get_var_name().get_name()

    def check_rep(self):
        assert len(self.children) == 2
        assert isinstance(self.children[0], InComp)
        assert isinstance(self.children[1], Operator) and self.children[1].text == ':'


class SpeciesList(TrunkNode):
    def get_all_species(self):
        return cast(List[Species], self.children[::2])

    def check_rep(self):
        assert len(self.children) == 0 or len(self.children) % 2 == 1
        for child in self.children[::2]:
            assert isinstance(child, Species)
        for child in self.children[1::2]:
            assert isinstance(child, LeafNode) and child.text == '+'


class Reaction(TrunkNode):
    def get_name(self):
        if self.children[0] is None:
            return None
        return cast(ReactionName, self.children[0]).get_name()

    def get_reactants(self):
        return cast(SpeciesList, self.children[1])

    def get_products(self):
        return cast(SpeciesList, self.children[3])

    def get_rate_law(self):
        return cast(ArithmeticExpr, self.children[5])

    def check_rep(self):
        assert len(self.children) == 7  # name reactants -> products ; rate_law END_MARKER
        assert self.children[0] is None or isinstance(self.children[0], ReactionName)
        assert isinstance(self.children[1], SpeciesList)
        assert isinstance(self.children[3], SpeciesList)
        assert isinstance(self.children[5], ArithmeticExpr)


class Assignment(TrunkNode):
    def get_maybein(self):
        return cast(MaybeIn, self.children[0])

    def get_name(self):
        return self.get_maybein().get_var_name().get_name()

    def get_value(self):
        return cast(ArithmeticExpr, self.children[2])

    def check_rep(self):
        assert len(self.children) == 3
        assert isinstance(self.children[0], MaybeIn)
        assert isinstance(self.children[1], Operator) and self.children[1].text == '='
        assert isinstance(self.children[2], ArithmeticExpr)


class VarModifier(Keyword):
    def check_rep(self):
        assert self.text in ('const', 'var')


class TypeModifier(Keyword):
    def check_rep(self):
        assert self.text in ('species', 'compartment', 'formula')


class DeclModifiers(TrunkNode):
    '''Represents the prefix modifiers to a declaration.
    
    Note that this is special in that the Lark parse tree, this node may have one or two children.
    But here it always has two: [DeclVarModifier, DeclTypeModifier]. At most one of those may be
    None.
    '''
    def __init__(self, parent: Optional['TrunkNode'], children: List[TreeNode], range_: SrcRange):
        super().__init__(parent, children, range_)
        self.children = children
        self.check_rep()

    def get_var_modifier(self):
        return cast(Optional[VarModifier], self.children[0])

    def get_type_modifier(self):
        return cast(Optional[TypeModifier], self.children[1])

    def get_variab(self):
        var_mod = self.get_var_modifier()
        if var_mod is None:
            return Variability.UNKNOWN
        return Variability.CONSTANT if var_mod == 'const' else Variability.VARIABLE

    def get_type(self):
        type_mod = self.get_type_modifier()
        if type_mod is None:
            return SymbolType.UNKNOWN

        return {
            'species': SymbolType.SPECIES,
            'compartment': SymbolType.COMPARTMENT,
            'formula': SymbolType.PARAMETER,
        }[type_mod.text]

    def check_rep(self):
        assert len(self.children) == 2
        assert isinstance(self.children[0], VarModifier)
        assert isinstance(self.children[1], TypeModifier)


class DeclarationAssignment(TrunkNode):
    def get_value(self):
        return cast(ArithmeticExpr, self.children[1])

    def check_rep(self):
        assert len(self.children) == 2
        assert isinstance(self.children[0], Operator) and self.children[0].text == '='
        assert isinstance(self.children[1], ArithmeticExpr)


class DeclarationItem(TrunkNode):
    def check_rep(self):
        assert len(self.children) == 2
        assert isinstance(self.children[0], MaybeIn)
        assert self.children[1] is None or isinstance(self.children[1], DeclarationAssignment)


class Declaration(TrunkNode):
    def get_modifiers(self):
        return cast(DeclModifiers, self.children[1])

    def check_rep(self):
        assert len(self.children) >= 3
        assert isinstance(self.children[0], DeclModifiers)


# TODO
class Annotation(TrunkNode):
    pass


def resolve_var_name(tree) -> NameItem:
    '''Resolve a var_name tree, i.e. one parsed from $A or A.
    '''
    assert len(tree.children) == 2

    return NameItem(tree.children[0], tree.children[1])


def resolve_maybein(tree) -> NameMaybeIn:
    assert len(tree.children) == 2

    name_item = resolve_var_name(tree.children[0])
    if tree.children[1] is not None:
        # skip "in"
        comp_item = resolve_var_name(tree.children[1].children[1])
    else:
        comp_item = None

    return NameMaybeIn(name_item, comp_item)


# TODO move this into a class called 'SpeciesList' so that it is an instance method
def resolve_species_list(tree):
    species_list = list()

    for species in tree.children:
        # A plus sign
        if isinstance(species, Token):
            continue
        assert species.data == 'species'
        assert not isinstance(species, str)
        stoich = None
        var_name: Tree
        assert len(species.children) == 2
        if species.children[0] is None:
            stoich = 1
        else:
            stoich = float(species.children[0])

        var_name = species.children[1]

        name_token = var_name.children[-1]
        assert isinstance(name_token, Token)
        species_list.append(Species(stoich, name_token))

    return species_list
