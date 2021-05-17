

# Helper classes to hold name structures

from typing import Callable, Optional, TypeVar, Union
from lark.lexer import Token
from lark.tree import Tree
from stibium.ant_types import Assignment, Atom, Declaration, DeclarationAssignment, DeclarationItem, InComp, Keyword, MaybeIn, Name, NameItem, NameMaybeIn, Number, Operator, Power, Product, Reaction, ReactionName, Species, SpeciesList, Sum, TrunkNode, TypeModifier, VarModifier, VarName
from stibium.symbols import AbstractScope, BaseScope

from stibium.types import SrcRange, SymbolType, Variability
from stibium.utils import get_range


TREE_MAP = {
    'var_name': VarName,
    'in_comp': InComp,
    'maybein': MaybeIn,
    'reaction_name': ReactionName,
    'reaction': Reaction,
    'species': Species,
    'species_list': SpeciesList,
    'assignment': Assignment,
    'declaration': Declaration,
    'declaration_item': DeclarationItem,
    'decl_assignment': DeclarationAssignment,
    'var_modifier': VarModifier,
    'type_modifier': TypeModifier,
    # TODO declaration_modifiers need special handling
    'sum': Sum,
    'product': Product,
    'power': Power,
    'atom': Atom,
    # TODO more
}


T = TypeVar('T')
def optional_transform(tree: Optional[Union[Tree, str]], fn: Callable[[Tree], T]) -> Optional[T]:
    if tree is None:
        return None

    assert isinstance(tree, Tree)
    return fn(tree)


def transform_lark_tree(tree: Tree):
    scope = BaseScope()
    for suite in tree.children:
        if isinstance(suite, Token):
            assert suite.type == 'error_token'
            continue

        assert isinstance(suite, Tree)

        if suite.data == 'error_node':
            continue

        if suite.data == 'suite':
            child = suite.children[0]
            if child is None:  # empty statement
                continue
            assert isinstance(child, Tree)

            if child.data == 'reaction':
                transform_reaction(child)
            elif child.data == 'assignment':
                transform_assignment(child)
            elif child.data == 'declaration':
                transform_declaration(child)
            elif child.data == 'annotation':
                pass  #TODO
            else:
                pass  #TODO


def transform_operator(token: Token):
    return Operator(get_range(token), token.value, token.type)


def transform_keyword(token: Token):
    return Keyword(get_range(token), token.value)


def transform_name(token: Token):
    return Name(get_range(token), token.value)


def transform_number(token: Token):
    return Number(get_range(token), token.value)


def transform_varname(tree: Tree):
    '''Resolve a var_name tree, i.e. one parsed from $A or A.
    '''
    assert len(tree.children) == 2

    const_op = None
    if tree.children[0] is not None:
        assert isinstance(tree.children[0], Token)
        const_op = transform_operator(tree.children[0])

    assert isinstance(tree.children[1], Token)
    return VarName(get_range(tree),
        (const_op, transform_name(tree.children[1])))


def transform_incomp(tree: Tree):
    assert isinstance(tree.children[0], Token) and tree.children[0].value == 'in'
    assert isinstance(tree.children[1], Tree)

    children = (transform_keyword(tree.children[0]), transform_varname(tree.children[1]))
    return InComp(get_range(tree), children)


def transform_maybein(tree: Tree):
    assert len(tree.children) == 2
    assert isinstance(tree.children[0], Tree)

    varname = transform_varname(tree.children[0])
    incomp = None
    if tree.children[0] is not None:
        assert isinstance(tree.children[1], Tree)
        incomp = transform_incomp(tree.children[1])
    
    return MaybeIn(get_range(tree), (varname, incomp))


def transform_reaction_name(tree: Tree):
    assert len(tree.children) == 2
    assert isinstance(tree.children[0], Tree)
    assert isinstance(tree.children[1], Token) and tree.children[1].value == ':'

    children = (transform_maybein(tree.children[0]), transform_operator(tree.children[1]))
    return ReactionName(get_range(tree), children)


def transform_species(tree: Tree):
    assert isinstance(tree.children[1], Tree)
    stoich = None
    if tree.children[0] is None:
        assert isinstance(tree.children[0], Token)
        stoich = transform_number(tree.children[0])
    
    return Species(get_range(tree), (stoich, transform_varname(tree)))


# TODO move this into a class called 'SpeciesList' so that it is an instance method
def transform_species_list(tree: Tree):
    children = list()

    for i, child in enumerate(tree.children):
        if i % 2 == 0:
            assert isinstance(child, Tree)
            children.append(transform_species(child))
        else:
            assert isinstance(child, Token)
            children.append(transform_operator(child))

    return SpeciesList(get_range(tree), children)


def transform_arithmetic_expr(tree: Union[Tree, Token]):
    print('arithmetic expr not implemented')
    return None


def transform_reaction(tree: Tree):
    assert len(tree.children) == 7

    reaction_name = optional_transform(tree.children[0], transform_reaction_name)

    assert isinstance(tree.children[1], Tree)  # reactants
    assert isinstance(tree.children[2], Token)  # arrow
    assert isinstance(tree.children[3], Tree)  # products
    assert isinstance(tree.children[4], Token)  # semicolon
    assert isinstance(tree.children[5], Tree)  # rate law

    incomp = optional_transform(tree.children[6], transform_incomp)

    children = (reaction_name,
                transform_species_list(tree.children[1]),
                transform_operator(tree.children[2]),
                transform_species_list(tree.children[3]),
                transform_operator(tree.children[4]),
                transform_arithmetic_expr(tree.children[5]),
                incomp)

    return Reaction(get_range(tree), children)


def transform_assignment(tree: Tree):
    assert isinstance(tree.children[0], Tree)
    assert isinstance(tree.children[1], Token) and tree.children[1].value == '='
    assert isinstance(tree.children[2], Tree) or isinstance(tree.children[2], Token)
    children = (transform_maybein(tree.children[0]),
                transform_operator(tree.children[1]),
                transform_arithmetic_expr(tree.children[2]))

    return Assignment(get_range(tree), children)
