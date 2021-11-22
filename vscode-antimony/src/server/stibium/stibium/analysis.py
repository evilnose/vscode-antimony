
import logging
from stibium.ant_types import Annotation, ArithmeticExpr, Assignment, Declaration, ErrorNode, ErrorToken, FileNode, Function, InComp, LeafNode, Model, Name, Reaction, SimpleStmt, TreeNode, TrunkNode
from .types import ASTNode, Issue, SymbolType, SyntaxErrorIssue, UnexpectedEOFIssue, UnexpectedNewlineIssue, UnexpectedTokenIssue, Variability, SrcPosition
from .symbols import AbstractScope, BaseScope, FunctionScope, ModelScope, QName, SymbolTable

from dataclasses import dataclass
from typing import Any, List, Optional, Set, cast
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
        self.table = SymbolTable()
        self.root = root
        base_scope = BaseScope()
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
                }[stmt.__class__.__name__](base_scope, stmt)
                self.handle_child_incomp(base_scope, stmt)
        
        self.semantic_issues = self.table.issues
        self.syntax_issues = list()
        self._record_syntax_issues()

    def _record_syntax_issues(self):
        lines = set()
        for node in self.root.children:
            if node is None:
                continue
            issue = None
            # isinstance() is too slow here
            if type(node) == ErrorToken:
                node = cast(ErrorToken, node)
                if node.text.strip() == '':
                    # this must be an unexpected newline
                    issue = UnexpectedNewlineIssue(node.range.start)
                else:
                    issue = UnexpectedTokenIssue(node.range, node.text)
            elif type(node) == ErrorNode:
                node = cast(ErrorNode, node)
                last_leaf = node.last_leaf()
                if last_leaf and last_leaf.next is None:
                    issue = UnexpectedEOFIssue(last_leaf.range)

            # only one issue per line
            if issue and issue.range.start.line not in lines:
                self.syntax_issues.append(issue)
                lines.add(issue.range.start.line)

    def resolve_qname(self, qname: QName):
        return self.table.get(qname)

    def get_all_names(self) -> Set[str]:
        # TODO temporary method to satisfy auto-completion
        return self.table.get_all_names()

    def get_issues(self) -> List[Issue]:
        # no deepcopy because issues should be frozen
        return (self.semantic_issues + self.syntax_issues).copy()

    def get_unique_name(self, prefix: str):
        return self.table.get_unique_name(prefix)

    def handle_child_incomp(self, scope: AbstractScope, node: TrunkNode):
        '''Find all `incomp` nodes among the descendants of node and record the compartment names.'''
        for child in node.descendants():
            # isinstance() is too slow here
            if child and type(child) == InComp:
                child = cast(InComp, child)
                self.table.insert(QName(scope, child.get_comp().get_name()), SymbolType.Compartment)

    def handle_arith_expr(self, scope: AbstractScope, expr: TreeNode):
        # TODO handle dummy tokens
        if not hasattr(expr, 'children'):
            if type(expr) == Name:
                leaf = cast(Name, expr)
                self.table.insert(QName(scope, leaf), SymbolType.Parameter)
        else:
            expr = cast(TrunkNode, expr)
            for leaf in expr.scan_leaves():
                if type(leaf) == Name:
                    leaf = cast(Name, leaf)
                    self.table.insert(QName(scope, leaf), SymbolType.Parameter)

    def handle_reaction(self, scope: AbstractScope, reaction: Reaction):
        name = reaction.get_name()
        if name is not None:
            self.table.insert(QName(scope, name), SymbolType.Reaction, reaction)
        # else:
        #     reaction_name = self.table.get_unique_name('_J', scope)
        #     reaction_range = get_tree_range(tree)
        #     reaction_token = tree.children[3]

        for species in chain(reaction.get_reactants(), reaction.get_products()):
            self.table.insert(QName(scope, species.get_name()), SymbolType.Species)

        self.handle_arith_expr(scope, reaction.get_rate_law())

    def handle_assignment(self, scope: AbstractScope, assignment: Assignment):
        self.table.insert(QName(scope, assignment.get_name()), SymbolType.Parameter,
                            value_node=assignment)
        self.handle_arith_expr(scope, assignment.get_value())

    def resolve_variab(self, tree) -> Variability:
        return {
            'var': Variability.VARIABLE,
            'const': Variability.CONSTANT,
        }[tree.data]

    def resolve_var_type(self, tree) -> SymbolType:
        return {
            'species': SymbolType.Species,
            'compartment': SymbolType.Compartment,
            'formula': SymbolType.Parameter,
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
            # If there is value assignment (value is not None), then record the declaration item
            # as the value node. Otherwise put None. See that we can't directly put "value" as
            # argument "valud_node" since they are different things
            value_node = item if value else None
            self.table.insert(QName(scope, name), stype, declaration, value_node)
            if value:
                self.handle_arith_expr(scope, value)
    
    def handle_annotation(self, scope: AbstractScope, annotation: Annotation):
        name = annotation.get_var_name().get_name()
        # TODO(Gary) maybe we can have a narrower type here, since annotation is restricted only to
        # species or compartments? I'm not sure. If that's the case though, we'll need union types.
        qname = QName(scope, name)
        self.table.insert(qname, SymbolType.Parameter)
        self.table.insert_annotation(qname, annotation)


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
