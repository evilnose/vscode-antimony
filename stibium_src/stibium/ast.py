
from .types import ASTNode, SymbolType, Variability, SrcPosition
from .symbols import AbstractScope, BaseScope, FunctionScope, ModelScope, QName, SymbolTable
from .utils import get_range

from dataclasses import dataclass
from typing import Any, List, Optional
from lark.lexer import Token
from lark.tree import Tree


def get_qname_at_position(root: Tree, pos: SrcPosition) -> Optional[QName]:
    '''Returns (context, token) the given position. `token` may be None if not found.
    '''
    def within_range(pos: SrcPosition, node: ASTNode):
        range_ = get_range(node)
        return pos >= range_.start and pos < range_.end

    node = root
    model = None
    func = None
    while not isinstance(node, Token):
        if node.data == 'model':
            model = str(node.children[1])
        elif node.data == 'function':
            func = str(node.children[1])

        for child in node.children:
            if child is None:
                continue
            assert isinstance(child, Token) or isinstance(child, Tree)
            if within_range(pos, child):
                node = child
                break
        else:
            # Didn't find it
            return None

    assert not (model is not None and func is not None)
    if model:
        scope = ModelScope(model)
    elif func:
        scope = FunctionScope(func)
    else:
        scope = BaseScope()

    return QName(scope, node)


class AntTreeAnalyzer:
    def __init__(self, root: Tree):
        self.issues = list()
        self.table = SymbolTable()
        self.root = root
        self.handle_parse_tree(root)

    def handle_parse_tree(self, tree):
        context = BaseScope()
        for suite in tree.children:
            if isinstance(suite, Token):
                assert suite.type == 'error_token'
                continue

            if suite.data == 'error_node':
                continue

            if suite.data == 'suite':
                child = suite.children[0]
                if child is None:  # empty statement
                    continue

                if child.data == 'reaction':
                    self.handle_reaction(context, child)
                elif child.data == 'assignment':
                    self.handle_assignment(context, child)
                elif child.data == 'declaration':
                    self.handle_declaration(context, child)

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

    def handle_formula(self, context: AbstractContext, tree: Tree):
        # TODO handle dummy tokens
        def pred(t):
            return isinstance(t, Token) and t.type == 'NAME'

        for parameter in tree.scan_values(pred):
            assert isinstance(parameter, Token)
            self.record_issues(
                self.table.insert(QName(context, parameter), SymbolType.PARAMETER)
            )

    def handle_reaction(self, context, tree):
        if tree.children[0] is not None:
            name_mi = resolve_maybein(tree.children[0].children[0])
            name = str(name_mi.name_item.name_tok)
            token = name_mi.name_item.name_tok
            self.record_issues(
                self.table.insert(QName(context, token), SymbolType.REACTION, tree)
            )
        # else:
        #     reaction_name = self.table.get_unique_name(context, '_J')
        #     reaction_range = get_range(tree)
        #     reaction_token = tree.children[3]

        # Skip ";"
        species_list = resolve_species_list(tree.children[1])
        # Skip "->"
        species_list += resolve_species_list(tree.children[3])

        for species in species_list:
            self.record_issues(
                self.table.insert(QName(context, species.name), SymbolType.SPECIES)
            )

        # Skip ";"
        self.handle_formula(context, tree.children[5])

    def handle_assignment(self, context, tree):
        name = tree.children[0]
        value = tree.children[2]
        name_mi = resolve_maybein(name)
        self.record_issues(
            self.table.insert(QName(context, name_mi.name_item.name_tok), SymbolType.PARAMETER,
                              value_node=tree)
        )
        self.handle_formula(context, value)

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

    def handle_declaration(self, context, tree):
        # TODO add modifiers in table
        modifiers = tree.children[0]
        # TODO deal with variability
        variab = Variability.UNKNOWN
        stype = SymbolType.PARAMETER
        if len(modifiers.children) == 1:
            mod = modifiers.children[0]
            if mod.data in ('const', 'var'):
                variab = self.resolve_variab(mod)
            else:
                stype = self.resolve_var_type(mod)
        elif len(modifiers.children) == 2:
            variab = self.resolve_variab(modifiers.children[0])
            stype = self.resolve_var_type(modifiers.children[1])

        # Skip comma separators
        for item in tree.children[1::2]:
            assert len(item.children) == 2
            name_mi = resolve_maybein(item.children[0])

            # Only store the value tree if the assignment node is not None
            value_tree = item if item.children[1] else None

            # TODO update variability
            self.record_issues(
                self.table.insert(QName(context, name_mi.name_item.name_tok), stype, tree,
                                  value_tree)
            )
            # TODO add value in table
            if item.children[1] is not None:
                # TODO record value
                pass


def get_ancestors(node: ASTNode):
    ancestors = list()
    while True:
        parent = getattr(node, 'parent')
        if parent is None:
            break
        ancestors.append(parent)
        node = parent

    return ancestors


def find_node(nodes: List[Tree], data: str):
    for node in nodes:
        if node.data == data:
            return node
    return None


def get_context(node: ASTNode):
    '''Create the exact context of a node.'''
    ancestors = get_ancestors(node)
    model = find_node(ancestors, 'model')
    if model:
        return ModelScope('TODO')
