
from .types import ASTNode, SymbolType, Variability, SrcPosition, Species
from .symbols import AbstractContext, BaseContext, FunctionContext, ModelContext, QName, SymbolTable
from .utils import get_range

from dataclasses import dataclass
from typing import Any, List, Optional
from lark.lexer import Token
from lark.tree import Tree


# Helper classes to hold name structures
@dataclass
class NameItem:
    const_tok: Optional[Token]
    name_tok: Token


@dataclass
class NameMaybeIn:
    name_item: NameItem
    comp_item: Optional[NameItem]


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
        context = ModelContext(model)
    elif func:
        context = FunctionContext(func)
    else:
        context = BaseContext()

    return QName(context, node)


@dataclass
class SymbolDatum:
    token: Token
    type: SymbolType
    # TODO add more fields like variability, etc.


@dataclass
class TreeResult:
    '''Represents the result obtained after walking a syntax tree.'''
    logical_obj: Any
    '''This represents data that can be logically interpreted as part of a bio model,
    such as Species, Reaction, etc.
    '''
    symbol_data: List[SymbolDatum]
    '''This represents symbol data that is useful for semantic analysis (diagnostics)
    '''


def handle_species_list(tree):
    species_list = list()
    symbol_list = list()

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
        species_list.append(Species(stoich, str(name_token)))
        symbol_list.append(SymbolDatum(name_token, SymbolType.SPECIES))

    return TreeResult(species_list, symbol_list)


class AntTreeAnalyzer:
    def __init__(self, root: Tree):
        self.issues = list()
        self.table = SymbolTable()
        self.root = root
        self.handle_parse_tree(root)

    def handle_parse_tree(self, tree):
        context = BaseContext()
        for suite in tree.children:
            if isinstance(suite, Token):
                assert suite.type == 'error_token'
                continue

            if suite.data == 'error_node':
                continue

            if suite.data == 'full_statement':
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

    def resolve_var_name(self, tree) -> NameItem:
        '''Resolve a var_name tree, i.e. one parsed from $A or A.
        '''
        assert len(tree.children) == 2

        return NameItem(tree.children[0], tree.children[1])

    def resolve_name_maybe_in(self, tree) -> NameMaybeIn:
        assert len(tree.children) == 2

        name_item = self.resolve_var_name(tree.children[0])
        if tree.children[1] is not None:
            # skip "in"
            comp_item = self.resolve_var_name(tree.children[1].children[1])
        else:
            comp_item = None

        return NameMaybeIn(name_item, comp_item)

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
            name_mi = self.resolve_name_maybe_in(tree.children[0].children[0])
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
        species_symbols = handle_species_list(tree.children[1]).symbol_data
        # Skip "->"
        species_symbols += handle_species_list(tree.children[3]).symbol_data

        for sym_data in species_symbols:
            assert sym_data.type == SymbolType.SPECIES
            self.record_issues(
                self.table.insert(QName(context, sym_data.token), SymbolType.SPECIES)
            )

        # Skip ";"
        self.handle_formula(context, tree.children[5])

    def handle_assignment(self, context, tree):
        name = tree.children[0]
        value = tree.children[2]
        name_mi = self.resolve_name_maybe_in(name)
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
            name_mi = self.resolve_name_maybe_in(item.children[0])

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
        return ModelContext('TODO')
