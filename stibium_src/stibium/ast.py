
from stibium.ant_types import Annotation, ArithmeticExpr, Assignment, Declaration, ErrorNode, ErrorToken, FileNode, Function, LeafNode, Model, Name, Reaction, SimpleStmt, TreeNode, TrunkNode
from .types import ASTNode, SymbolType, Variability, SrcPosition
from .symbols import AbstractScope, BaseScope, FunctionScope, ModelScope, QName, SymbolTable
from .utils import get_range

from dataclasses import dataclass
from typing import Any, List, Optional
from itertools import chain
from lark.lexer import Token
from lark.tree import Tree


def get_qname_at_position(root: FileNode, pos: SrcPosition) -> Optional[QName]:
    '''Returns (context, token) the given position. `token` may be None if not found.
    '''
    def within_range(pos: SrcPosition, node: TreeNode):
        return pos >= node.range.start and pos < node.range.end

    node: TreeNode = root
    model: Optional[Name] = None
    func: Optional[Name] = None
    while not isinstance(node, LeafNode):
        if isinstance(node, Model):
            assert model is None
            model = node.get_name()
        elif isinstance(node, Function):
            assert func is None
            func = node.get_name()

        for child in node.children:
            if child is None:
                continue

            if within_range(pos, child):
                node = child
                break
        else:
            # Didn't find it
            return None

    # can't have nested models/functions
    assert not (model is not None and func is not None)
    if model:
        scope = ModelScope(str(model))
    elif func:
        scope = FunctionScope(str(func))
    else:
        scope = BaseScope()

    return QName(scope, node)


class AntTreeAnalyzer:
    def __init__(self, root: FileNode):
        self.issues = list()
        self.table = SymbolTable()
        self.root = root
        for child in root.children:
            if isinstance(child, ErrorToken):
                continue
            if isinstance(child, ErrorNode):
                continue
            if isinstance(child, SimpleStmt):
                stmt = child.get_stmt()
                if stmt is None:
                    continue

                {
                    'Reaction': self.handle_reaction,
                    'Assignment': self.handle_assignment,
                    'Declaration': self.handle_declaration,
                    'Annotation': self.handle_annotation,
                }[stmt.__class__.__name__](BaseScope(), stmt)

    def resolve_qname(self, qname: QName):
        return self.table.get(qname)

    def get_all_names(self):
        # TODO temporary method to satisfy auto-completion
        # TODO also remove the same method from table
        return self.table.get_all_names()

    def record_issues(self, issues):
        # TODO more sophisticated stuff? e.g. separate errors, warnings, syntax errors, semantic errors>
        self.issues += issues

    def get_issues(self):
        return self.issues

    def handle_arith_expr(self, scope: AbstractScope, expr: TreeNode):
        # TODO handle dummy tokens
        for leaf in expr.scan_leaves():
            if isinstance(leaf, Name):
                self.record_issues(
                    self.table.insert(QName(scope, leaf), SymbolType.PARAMETER)
                )

    def handle_reaction(self, scope: AbstractScope, reaction: Reaction):
        name = reaction.get_name()
        if name is not None:
            self.record_issues(
                self.table.insert(QName(scope, name), SymbolType.REACTION, reaction)
            )
        # else:
        #     reaction_name = self.table.get_unique_name(context, '_J')
        #     reaction_range = get_range(tree)
        #     reaction_token = tree.children[3]

        for species in chain(reaction.get_reactant_list().get_all_species(),
                             reaction.get_product_list().get_all_species()):
            self.record_issues(
                self.table.insert(QName(scope, species.get_name()), SymbolType.SPECIES)
            )

        self.handle_arith_expr(scope, reaction.get_rate_law())

    def handle_assignment(self, scope: AbstractScope, assignment: Assignment):
        self.record_issues(
            self.table.insert(QName(scope, assignment.get_name()), SymbolType.PARAMETER,
                              value_node=assignment)
        )
        self.handle_arith_expr(scope, assignment.get_value())

    def resolve_variab(self, tree) -> Variability:
        return {
            'var': Variability.VARIABLE,
            'const': Variability.CONSTANT,
        }[tree.data]

    def resolve_var_type(self, tree) -> SymbolType:
        return {
            'species': SymbolType.SPECIES,
            'compartment': SymbolType.COMPARTMENT,
            'formula': SymbolType.PARAMETER,
        }[tree.data]

    def handle_declaration(self, scope: AbstractScope, declaration: Declaration):
        # TODO add modifiers in table
        modifiers = declaration.get_modifiers()
        # TODO deal with variability
        variab = modifiers.get_variab()
        stype = modifiers.get_type()

        # Skip comma separators
        for item in declaration.get_items():
            name = item.get_maybein().get_var_name().get_name()
            value = item.get_value()

            # TODO update variability
            self.record_issues(
                self.table.insert(QName(scope, name), stype, declaration, value)
            )
            if value:
                self.handle_arith_expr(scope, value)
    
    def handle_annotation(self, scope: AbstractScope, annotation: Annotation):
        pass


# def get_ancestors(node: ASTNode):
#     ancestors = list()
#     while True:
#         parent = getattr(node, 'parent')
#         if parent is None:
#             break
#         ancestors.append(parent)
#         node = parent

#     return ancestors


# def find_node(nodes: List[Tree], data: str):
#     for node in nodes:
#         if node.data == data:
#             return node
#     return None
