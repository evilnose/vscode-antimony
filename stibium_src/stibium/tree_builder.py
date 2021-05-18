

# Helper classes to hold name structures

from typing import Callable, Optional, TypeVar, Union

from lark.lexer import Token
from lark.tree import Tree

from stibium.ant_types import (Annotation, ArithmeticExpr, Assignment, Atom,
                               Declaration, DeclarationAssignment,
                               DeclarationItem, ErrorNode, ErrorToken,
                               FileNode, InComp, Keyword, LeafNode, MaybeIn,
                               Name, Number, Operator,
                               Power, Product, Reaction, ReactionName,
                               SimpleStmt, Species, SpeciesList, StmtSeparator,
                               Sum, TrunkNode, TypeModifier, VarModifier,
                               VarName)
from stibium.symbols import AbstractScope, BaseScope
from stibium.types import ASTNode, SrcRange, SymbolType, Variability
from stibium.utils import get_range

# Use None to indicate that this node should have exactly one child and should be skilled
TREE_MAP = {
    'NAME': Name,
    'NUMBER': Number,
    'STMT_SEPARATOR': StmtSeparator,
    'ERROR_TOKEN': ErrorToken,
    'EQUAL': Operator,
    # TODO need to add more operators
    'error_node': ErrorNode,
    'root': FileNode,
    'simple_stmt': SimpleStmt,
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


def transform_tree(tree: Optional[Union[Tree, str]]):
    if tree is None:
        return None

    if isinstance(tree, str):
        assert isinstance(tree, Token)
        # TODO process token
        cls = TREE_MAP[tree.type]
        return cls(get_range(tree), tree.value)
    else:
        if tree.data == 'sum':
            return Sum(get_range(tree), tuple())  # TODO
        if tree.data == 'annotation':
            return Annotation(get_range(tree), tuple())  # TODO

        cls = TREE_MAP[tree.data]
        # if cls is None:
        #     # delegate
        #     assert len(tree.children) == 1
        #     return transform_tree(tree.children[0])

        children = tuple(transform_tree(child) for child in tree.children)
        return cls(get_range(tree), children)
