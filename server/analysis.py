
from dataclasses import dataclass
from typing import Optional
from lark.lexer import Token
from lark.tree import Tree
from classes import SymbolType, Variability

from symbols import AbstractContext, BaseContext, ModelContext, SymbolTable
from utils import get_range


# Helper classes to hold name structures
@dataclass
class NameItem:
    const_tok: Optional[Token]
    name_tok: Token


@dataclass
class NameMaybeIn:
    name_item: NameItem
    comp_item: Optional[NameItem]


class AntimonyTreeAnalyzer:
    def __init__(self, root: Tree):
        self.issues = list()
        self.table = SymbolTable()
        self.handle_parse_tree(root)

    def get_all_names(self):
        # TODO temporary method to satisfy auto-completion
        # TODO also remove the same method from table
        return self.table.get_all_names()

    def record_issues(self, issues):
        # TODO more sophisticated stuff? e.g. separate errors, warnings, syntax errors, semantic errors>
        self.issues += issues

    def get_issues(self):
        return self.issues

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

    def handle_species_list(self, context, tree):
        for species in tree.children:
            # A plus sign
            if isinstance(species, Token):
                continue
            assert species.data == 'species'
            assert not isinstance(species, str)
            stoich = None
            var_name: Tree
            if len(species.children) == 1:
                stoich = '1'
                var_name = species.children[0]
            else:
                assert len(species.children) == 2
                stoich = str(species.children[0])
                var_name = species.children[1]

            name_token = var_name.children[-1]
            assert isinstance(name_token, Token)
            name = str(name_token)
            # TODO create a helper function that masks table.update_type and automatically add
            # the errors
            self.record_issues(
                self.table.insert(context, name, SymbolType.SPECIES, name_token, None)
            )

    def handle_formula(self, context: AbstractContext, tree: Tree):
        # TODO handle dummy tokens
        def pred(t):
            return isinstance(t, Token) and t.type == 'NAME'

        for parameter in tree.scan_values(pred):
            assert isinstance(parameter, Token)
            name = str(parameter)
            self.record_issues(
                self.table.insert(context, name, SymbolType.PARAMETER, parameter)
            )

    def handle_reaction(self, context, tree):
        if tree.children[0] is not None:
            name_mi = self.resolve_name_maybe_in(tree.children[0])
            name = str(name_mi.name_item.name_tok)
            token = name_mi.name_item.name_tok
            self.record_issues(
                self.table.insert(context, name, SymbolType.REACTION, token, tree)
            )
        # else:
        #     reaction_name = self.table.get_unique_name(context, '_J')
        #     reaction_range = get_range(tree)
        #     reaction_token = tree.children[3]

        # Skip ";"
        self.handle_species_list(context, tree.children[2])
        # Skip "->"
        self.handle_species_list(context, tree.children[4])
        # Skip ";"
        self.handle_formula(context, tree.children[6])

    def handle_assignment(self, context, tree):
        name = tree.children[0]
        value = tree.children[2]
        name_mi = self.resolve_name_maybe_in(name)
        self.record_issues(
            self.table.insert(context, str(name_mi.name_item.name_tok), SymbolType.PARAMETER,
                                  name_mi.name_item.name_tok)
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
        variab = Variability.UNKNOWN
        stype = SymbolType.UNKNOWN
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
            # TODO update variability
            self.record_issues(
                self.table.insert(context, str(name_mi.name_item.name_tok), stype,
                                  name_mi.name_item.name_tok, tree)
            )
            # TODO add value in table
            if item.children[1] is not None:
                # TODO record value
                pass
