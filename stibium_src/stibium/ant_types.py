import abc
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union, cast
from lark.lexer import Token
from lark.tree import Tree

from stibium.types import SrcRange, SymbolType, Variability


class TreeNode(abc.ABC):
    '''Basically either a TrunkNode or a LeafNode.
    This is not a dataclass to avoid inheritance issues. The attributes are there for static
    analysis.
    '''
    range: SrcRange
    parent: Optional['TrunkNode']

    def scan_leaves(self):
        '''Return all the leaf nodes that are descendants of this node (possibly including self)'''
        for leaf in _scan_leaves(self):
            yield leaf

    def next_sibling(self):
        if self.parent is None:
            return None

        for index, node in enumerate(self.parent.children):
            if node is self:
                if index == len(self.parent.children) - 1:
                    return None
                return self.parent.children[index + 1]
        return None

    def check_rep(self):
        pass


@dataclass
class TrunkNode(TreeNode):
    range: SrcRange
    children: Tuple[Optional['TreeNode'], ...] = field(repr=False)
    parent: Optional['TrunkNode'] = field(default=None, compare=False, repr=False)

    def descendants(self):
        '''Iterate over all descendants, including self and the None nodes.'''
        for child in self.children:
            if child is not None:
                if isinstance(child, LeafNode):
                    yield child
                else:
                    child = cast(TrunkNode, child)
                    for desc in child.descendants():
                        yield desc
        yield self


@dataclass
class LeafNode(TreeNode):
    range: SrcRange
    text: str
    parent: Optional['TrunkNode'] = field(default=None, compare=False, repr=False)
    prev: Optional['LeafNode'] = field(default=None, compare=False, repr=False)
    next: Optional['LeafNode'] = field(default=None, compare=False, repr=False)


def _scan_leaves(node: TreeNode):
    if isinstance(node, TrunkNode):
        for child in node.children:
            if child is not None:
                for leaf in _scan_leaves(child):
                    yield leaf
    else:
        assert isinstance(node, LeafNode)
        yield node


@dataclass
class ErrorNode(TrunkNode):
    '''ErrorNode is a tree of tokens that appear before an unexpected token (ErrorToken).

    In particular, if the tokens that appeared before the ErrorToken have not been able to form
    a statement yet, they would be collected into an ErrorNode. For example in a =?, 'a =' forms
    an error node, but in 'a = 5;?', there is no error node, since 'a = 5;' forms a complete
    statement, and we don't need to handle any dangling tokens before '?'.
    
    The error node does not have to contain only leaf nodes. It contains the best guess of the
    parser at that point, so one may see full nodes (e.g. NameMaybeIn) if there is no ambiguity
    at that point.
    '''
    pass


@dataclass
class ErrorToken(LeafNode):
    pass


class ArithmeticExpr(TreeNode):
    '''Base class for arithmetic expressions.'''
    pass


@dataclass
class Sum(ArithmeticExpr, TrunkNode):
    '''Arithmetic expression with an addition/subtraction root operator.'''
    pass


@dataclass
class Product(ArithmeticExpr, TrunkNode):
    '''Arithmetic expression with a multiplication/division root operator.'''
    pass


@dataclass
class Power(ArithmeticExpr, TrunkNode):
    '''Arithmetic expression with a power root operator.'''
    pass


# @dataclass
# class Negation(ArithmeticExpr, TrunkNode):
#     '''Arithmetic expression that represents a negation'''
#     children: Tuple['Operator', 'Atom'] = field(repr=False)


@dataclass
class Atom(TrunkNode, ArithmeticExpr):
    '''Atomic arithmetic expression.'''
    children: Tuple['Operator', Union[ArithmeticExpr, 'Number', 'VarName'], 'Operator'] = field(repr=False)
    # TODO also possible that children be '-' 'number' or '+' 'name', etc. Possibly create a new
    # rule called Factor that handles that?


class Name(LeafNode):
    def check_rep(self):
        assert bool(self.text)


class Number(LeafNode, ArithmeticExpr):
    def get_value(self):
        return float(self.text)
    
    def check_rep(self):
        self.get_value()


@dataclass
class Operator(LeafNode):
    pass


@dataclass
class Keyword(LeafNode):
    pass


@dataclass
class StringLiteral(LeafNode):
    pass


# NOTE for now, the EOF is constructed as a Newline with text being an empty string. In the future,
# we may want to add a special EOF class
@dataclass
class Newline(LeafNode):
    pass


@dataclass
class VarName(TrunkNode):
    children: Tuple[Optional[Operator], Name] = field(repr=False)

    def is_const(self):
        return self.children[0] is not None

    def get_name(self):
        return self.children[1]

    def get_name_text(self):
        return self.children[1].text


@dataclass
class InComp(TrunkNode):
    children: Tuple[Keyword, VarName] = field(repr=False)

    def get_comp(self) -> VarName:
        return self.children[1]


@dataclass
class NameMaybeIn(TrunkNode):
    children: Tuple[VarName, Optional[InComp]] = field(repr=False)

    def get_var_name(self):
        return self.children[0]
    
    def is_in_comp(self):
        return self.children[1] is not None

    def get_comp(self):
        return self.children[1].get_comp()


# # TODO move this to another class, e.g. logical/model types
# # TODO create new classes Name and Node to replace Token and Tree
# @dataclass
# class Species:
#     stoich: float
#     name: Token


@dataclass
class Species(TrunkNode):
    children: Tuple[Optional[Number], Optional[Operator], Name] = field(repr=False)
    
    def get_stoich(self):
        if self.children[0] is None:
            return 1

        return self.children[0].get_value()

    def is_const(self):
        return bool(self.children[1])

    def get_name(self):
        return self.children[2]

    def get_name_text(self):
        return self.get_name().text


@dataclass
class ReactionName(TrunkNode):
    '''Represents the 'J0:' at the start of the reaction.'''
    children: Tuple[NameMaybeIn, Operator] = field(repr=False)

    def get_maybein(self):
        return self.children[0]

    def get_name(self):
        return self.get_maybein().get_var_name().get_name()

    def get_name_text(self):
        return self.get_maybein().get_var_name().get_name_text()


@dataclass
class SpeciesList(TrunkNode):
    def get_all_species(self) -> List[Species]:
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
                    ArithmeticExpr, Optional[InComp]] = field(repr=False)

    def get_name(self):
        if self.children[0] is None:
            return None
        return self.children[0].get_name()

    def get_name_text(self):
        if self.children[0] is None:
            return None
        return self.children[0].get_name_text()

    def get_reactant_list(self) -> Optional[SpeciesList]:
        return self.children[1]

    def get_product_list(self) -> Optional[SpeciesList]:
        return self.children[3]

    def get_reactants(self) -> List[Species]:
        slist = self.get_reactant_list()
        if slist:
            return slist.get_all_species()
        return list()

    def get_products(self) -> List[Species]:
        slist = self.get_product_list()
        if slist:
            return slist.get_all_species()
        return list()

    def get_rate_law(self):
        return self.children[5]

    def is_reversible(self):
        assert self.children[2].text in ('->', '=>')
        return self.children[2].text == '=>'


@dataclass
class Assignment(TrunkNode):
    children: Tuple[NameMaybeIn, Operator, ArithmeticExpr] = field(repr=False)

    def get_maybein(self):
        return self.children[0]

    def get_name(self):
        return self.get_maybein().get_var_name().get_name()

    def get_name_text(self):
        return self.get_maybein().get_var_name().get_name_text()

    def get_value(self):
        return self.children[2]


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
    children: Tuple[Optional[VarModifier], Optional[TypeModifier]] = field(repr=False)

    def get_var_modifier(self):
        return self.children[0]

    def get_type_modifier(self):
        return self.children[1]

    def get_variab(self):
        var_mod = self.get_var_modifier()
        if var_mod is None:
            return Variability.UNKNOWN
        return Variability.CONSTANT if var_mod.text == 'const' else Variability.VARIABLE

    def get_type(self):
        type_mod = self.get_type_modifier()
        if type_mod is None:
            return SymbolType.Unknown

        return {
            'species': SymbolType.Species,
            'compartment': SymbolType.Compartment,
            'formula': SymbolType.Parameter,
        }[type_mod.text]

    def check_rep(self):
        assert bool(self.children[0]) or bool(self.children[1])


@dataclass
class DeclAssignment(TrunkNode):
    children: Tuple[Operator, ArithmeticExpr] = field(repr=False)

    def get_value(self):
        return self.children[1]


@dataclass
class DeclItem(TrunkNode):
    children: Tuple[NameMaybeIn, DeclAssignment] = field(repr=False)

    def get_maybein(self):
        return self.children[0]

    def get_decl_assignment(self):
        return self.children[1]

    def get_name(self):
        return self.get_maybein().get_var_name().get_name()

    def get_name_text(self):
        return self.get_maybein().get_var_name().get_name_text()

    def get_value(self):
        node = self.get_decl_assignment()
        if node is None:
            return None
        return node.get_value()


@dataclass
class Declaration(TrunkNode):
    def get_modifiers(self):
        return cast(DeclModifiers, self.children[0])

    def get_items(self):
        items = self.children[1::2]
        return cast(List[DeclItem], items)

    def check_rep(self):
        assert len(self.children) >= 3
        assert isinstance(self.children[0], DeclModifiers)
        assert isinstance(self.children[1], DeclItem)
        assert isinstance(self.children[2], Operator)


# TODO All below
@dataclass
class Annotation(TrunkNode):
    children: Tuple[VarName, Keyword, StringLiteral]

    def get_var_name(self):
        return self.children[0]

    def get_name_text(self):
        return self.get_var_name().get_name_text()

    def get_keyword(self):
        return self.children[1].text

    def get_uri(self):
        return self.children[2].text


@dataclass
class SimpleStmt(TrunkNode):
    children: Tuple[Union[Reaction, Assignment, Declaration, Annotation], Union[Operator, Newline]] = field(repr=False)

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
    children: Tuple[SimpleStmt, ...] = field(repr=False)
