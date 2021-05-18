from dataclasses import dataclass
from typing import List, Optional, Tuple, Union, cast
from lark.lexer import Token
from lark.tree import Tree

from stibium.types import SrcRange, SymbolType, Variability


@dataclass
class TreeNode:
    range: SrcRange

    def scan_leaves(self):
        '''Return all the leaf nodes that are descendants of this node (possibly including self)'''
        return _scan_leaves(self)

    def check_rep(self):
        pass


@dataclass
class TrunkNode(TreeNode):
    children: Tuple['TreeNode', ...]
    parent: Optional['TrunkNode'] = None


@dataclass
class LeafNode(TreeNode):
    text: str
    parent: Optional['TrunkNode'] = None


def _scan_leaves(node: TreeNode):
    if isinstance(node, TrunkNode):
        for child in node.children:
            _scan_leaves(child)
    else:
        assert isinstance(node, LeafNode)
        yield node


@dataclass
class ErrorNode(TreeNode):
    pass


@dataclass
class ErrorToken(LeafNode):
    pass


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


@dataclass
class Operator(LeafNode):
    pass


class Keyword(LeafNode):
    pass


@dataclass
class StmtSeparator(LeafNode):
    # text: Union[Literal[''], Literal['\n'], Literal['\r\n'], Literal[';']]
    pass


@dataclass
class VarName(TrunkNode):
    children: Tuple[Optional[Operator], Name]

    def is_const(self):
        return self.children[0] is not None

    def get_name(self):
        return self.children[1]

    def get_name_text(self):
        return str(self.children[1])


@dataclass
class InComp(TrunkNode):
    children: Tuple[Keyword, VarName]

    def get_comp(self) -> VarName:
        return cast(VarName, self.children[1])


@dataclass
class MaybeIn(TrunkNode):
    children: Tuple[VarName, Optional[InComp]]

    def get_var_name(self):
        return cast(VarName, self.children[0])
    
    def is_in_comp(self):
        return self.children[1] is not None

    def get_comp(self):
        return cast(InComp, self.children[1]).get_comp()


# # TODO move this to another class, e.g. logical/model types
# # TODO create new classes Name and Node to replace Token and Tree
# @dataclass
# class Species:
#     stoich: float
#     name: Token


@dataclass
class Species(TrunkNode):
    children: Tuple[Optional[Number], VarName]
    
    def get_stoich(self):
        if self.children[0] is None:
            return 1

        return cast(Number, self.children[0]).get_value()

    def get_var_name(self):
        return cast(VarName, self.children[1])

    def get_name(self):
        return self.get_var_name().get_name()


@dataclass
class ReactionName(TrunkNode):
    '''Represents the 'J0:' at the start of the reaction.'''
    children: Tuple[MaybeIn, Operator]

    def get_maybein(self):
        return cast(MaybeIn, self.children[0])

    def get_name(self):
        return self.get_maybein().get_var_name().get_name()

    def get_name_text(self):
        return self.get_maybein().get_var_name().get_name_text()


@dataclass
class SpeciesList(TrunkNode):
    def get_all_species(self):
        return cast(List[Species], self.children[::2])

    def check_rep(self):
        assert len(self.children) == 0 or len(self.children) % 2 == 1
        for child in self.children[::2]:
            assert isinstance(child, Species)
        for child in self.children[1::2]:
            assert isinstance(child, LeafNode) and child.text == '+'


@dataclass
class Reaction(TrunkNode):
    children: Tuple[Optional[ReactionName], SpeciesList, Operator, SpeciesList, Operator,
                    ArithmeticExpr, Optional[InComp]]

    def get_name(self):
        if self.children[0] is None:
            return None
        return cast(ReactionName, self.children[0]).get_name()

    def get_name_text(self):
        if self.children[0] is None:
            return None
        return cast(ReactionName, self.children[0]).get_name_text()

    def get_reactant_list(self):
        return cast(SpeciesList, self.children[1])

    def get_product_list(self):
        return cast(SpeciesList, self.children[3])

    def get_rate_law(self):
        return cast(ArithmeticExpr, self.children[5])


@dataclass
class Assignment(TrunkNode):
    children: Tuple[MaybeIn, Operator, ArithmeticExpr]
    def get_maybein(self):
        return cast(MaybeIn, self.children[0])

    def get_name(self):
        return self.get_maybein().get_var_name().get_name()

    def get_name_text(self):
        return self.get_maybein().get_var_name().get_name_text()

    def get_value(self):
        return cast(ArithmeticExpr, self.children[2])


@dataclass
class VarModifier(Keyword):
    # text: Union[Literal['const'], Literal['var']]
    pass


@dataclass
class TypeModifier(Keyword):
    # text: Union[Literal['species'], Literal['compartment'], Literal['formula']]
    pass


@dataclass
class DeclModifiers(TrunkNode):
    '''Represents the prefix modifiers to a declaration.
    
    Note that this is special in that the Lark parse tree, this node may have one or two children.
    But here it always has two: [DeclVarModifier, DeclTypeModifier]. At most one of those may be
    None.
    '''
    children: Tuple[Optional[VarModifier], Optional[TypeModifier]]

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
        assert bool(self.children[0]) or bool(self.children[1])


@dataclass
class DeclarationAssignment(TrunkNode):
    children: Tuple[Operator, ArithmeticExpr]

    def get_value(self):
        return cast(ArithmeticExpr, self.children[1])


@dataclass
class DeclarationItem(TrunkNode):
    children: Tuple[MaybeIn, DeclarationAssignment]

    def get_maybein(self):
        return self.children[0]

    def get_decl_assignment(self):
        return self.children[1]

    def get_var_name(self):
        return self.get_maybein().get_var_name()

    def get_value(self):
        return self.get_decl_assignment().get_value()


@dataclass
class Declaration(TrunkNode):
    def get_modifiers(self):
        return cast(DeclModifiers, self.children[0])

    def get_items(self):
        items = self.children[1::2]
        return cast(List[DeclarationItem], items)

    def check_rep(self):
        assert len(self.children) >= 3
        assert isinstance(self.children[0], DeclModifiers)
        assert isinstance(self.children[1], DeclarationItem)
        assert isinstance(self.children[2], Operator)


# TODO All below
@dataclass
class Annotation(TrunkNode):
    pass


@dataclass
class SimpleStmt(TrunkNode):
    children: Tuple[Union[Reaction, Assignment, Declaration, Annotation], StmtSeparator]

    def get_stmt(self):
        return self.children[0]


# TODO
@dataclass
class Model(TrunkNode):
    def get_name(self):
        assert False, 'Not implemented'


@dataclass
class Function(TrunkNode):
    def get_name(self):
        assert False, 'Not implemented'


@dataclass
class FileNode(TrunkNode):
    children: Tuple[SimpleStmt, ...]