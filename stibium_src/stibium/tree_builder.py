

# Helper classes to hold name structures
from dataclasses import dataclass
from typing import List, Optional

from lark.lexer import Token
from lark.tree import Tree

from stibium.types import SrcRange


@dataclass
class NameItem:
    const_tok: Optional[Token]
    name_tok: Token


@dataclass
class NameMaybeIn:
    name_item: NameItem
    comp_item: Optional[NameItem]


@dataclass
class TreeNode:
    range: SrcRange
    parent: Optional['TreeNode']


@dataclass
class TrunkNode(TreeNode):
    children: List['TreeNode']


@dataclass
class Name(TreeNode):
    text: str


@dataclass
class VarName(TrunkNode):
    def is_const(self):
        return self.children[0] is not None

    def get_name(self):
        return str(self.children[1])


@dataclass
class InComp(TrunkNode):
    def get_comp(self):
        return self.children[1]


@dataclass
class MaybeIn(TrunkNode):
    def get_var_name(self):
        return self.children[0]
    
    def is_in_comp(self):
        return self.children[1] is not None

    def get_comp(self):
        assert isinstance(self.children[1], InComp)
        return self.children[1].get_comp()



# TODO move this to another class, e.g. logical/model types
# TODO create new classes Name and Node to replace Token and Tree
@dataclass
class Species:
    stoich: float
    name: Token


class ReactionSpecies(TrunkNode):
    pass


@dataclass
class Reaction:
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
