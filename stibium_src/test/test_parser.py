from dataclasses import dataclass
from typing import List, NamedTuple, Optional, Tuple
from lark.tree import Tree
from stibium.ant_types import Declaration, FileNode, Reaction, SimpleStmt, Species, SpeciesList
from stibium.parse import AntimonyParser
from stibium.utils import formatted_code
from stibium.types import AntimonySyntaxError, SymbolType, Variability

import pytest


parser = AntimonyParser()


# TODO add more tests as more syntax features are added
@pytest.mark.parametrize('code', [
    'a = 12.5 * b',
    'J0: A + 3B -> 10C + $D; -12 * a * (4 + 3.332 ^ b);',
    '',
    '''
const A = 10, A_2
formula B, CCC = 2 * (B - 3)
var $B = 2 * 5 * k, EF, IAC
J0: A + 3A_2 -> 2.5C; took

baggins = 5;;;

gamgee = 10

i122 identity "http://identifiers.org/chebi/CHEBI:17234"'''
])
def test_formatted_code(code):
    tree = parser.parse(code)
    other_tree = parser.parse(code, recoverable=True)  # tree without error recovery
    assert tree == other_tree
    assert code == formatted_code(tree)


def test_parse_end_marker():
    '''Ensure this handles end marker well.'''
    tree = parser.parse('foo = 3.5')
    assert len(tree.children) == 1
    tree = parser.parse('foo = 3.5;')
    assert len(tree.children) == 2  # the second statement is from ';' to EOF and is empty
    assert isinstance(tree.children[1], SimpleStmt) and tree.children[1].children[0] is None


def assert_reaction(reaction: Reaction, expected_reactants: List[Tuple[float, str]],
                    expected_products: List[Tuple[float, str]], name: str = None):

    # structural assertions
    assert len(reaction.children) == 7
    assert reaction.get_name_text() == name

    reactants = reaction.get_reactants()
    products = reaction.get_products()

    if reactants:
        assert isinstance(reaction.get_reactant_list(), SpeciesList)
    else:
        assert reaction.get_reactant_list() is None

    if products:
        assert isinstance(reaction.get_product_list(), SpeciesList)
    else:
        assert reaction.get_product_list() is None

    # actual test case
    assert [(s.get_stoich(), s.get_name_text()) for s in reactants] == expected_reactants
    assert [(s.get_stoich(), s.get_name_text()) for s in products] == expected_products


@pytest.mark.parametrize('code,expected_args', [
    # basic
    ('J0: A -> 2B; 2 * k;', ('1/A', '2/B', 'J0')),
    # same name
    ('A -> 2A; 2 * k;', ('1/A', '2/A', None)),
    # multiple reactants/products and rare float format
    ('J_33: A + 3.2B12 -> 2e4C + 1.2D + 0E; 2 * k;', ('1/A,3.2/B12', '2e4/C,1.2/D,0/E', 'J_33')),
    # no reactants
    ('J: => 2e4C + 1.2D + 0E; 2 * k', ('', '2e4/C,1.2/D,0/E', 'J')),
    # no products
    ('J: 2A->;3+k;', ('2/A', '', 'J')),
    # no name
    ('A + 22B72_ => 1.4C; 1', ('1/A,22/B72_', '1.4/C', None)),
    # no name or reactants
    ('-> 1.4C; 1;', ('', '1.4/C', None)),
])
def test_parse_reaction(code: str, expected_args: Tuple[str, str, Optional[str]]):
    def parse_species_list(text: str):
        '''Helper for parsing expected species lists'''
        if not text:
            return []
        tokens = text.split(',')
        ret = list()
        for tok in tokens:
            subtoks = tok.split('/')
            assert len(subtoks) == 2
            stoich, name = subtoks
            ret.append((float(stoich), name))
        return ret

    # parse args using the baby test parser
    assert len(expected_args) == 3
    reactants = parse_species_list(expected_args[0])
    products = parse_species_list(expected_args[1])
    name = expected_args[2]

    tree = parser.parse(code)

    assert len(tree.children) in (1, 2)  # may or may not have a stmt_separator at the end
    stmt = tree.children[0]
    assert isinstance(stmt, SimpleStmt)

    reaction = stmt.get_stmt()
    assert isinstance(reaction, Reaction)

    assert_reaction(reaction, reactants, products, name)


def test_reaction_reversibility():
    tree = parser.parse('A -> B; 1')
    reaction = tree.children[0].children[0]
    assert isinstance(reaction, Reaction) and not reaction.is_reversible()

    tree = parser.parse('A => B; 1')
    reaction = tree.children[0].children[0]
    assert isinstance(reaction, Reaction) and reaction.is_reversible()


@pytest.mark.parametrize('code', [
    '1: A -> B;1',  # illegal name
    ':A->B;1',  # no name
    '->;1',  # no reactants or products
    "A->B;"  # no rate law
])
def test_parse_fail_reaction(code: str):
    '''Should fail for illegal reactions'''
    with pytest.raises(AntimonySyntaxError):
        parser.parse(code)


# Classes for easier testing
@dataclass
class DeclMod:
    variab: Variability
    type: SymbolType  # this is the formatted code of the value


@dataclass
class DeclItm:
    name: str
    value: str


@dataclass
class Decl:
    mod: DeclMod
    items: List[DeclItm]


@pytest.mark.parametrize('code,expected', [
    ('var a',
     Decl(mod=DeclMod(Variability.VARIABLE, SymbolType.UNKNOWN), items=[DeclItm('a', '')])),

    ('const a22', Decl(mod=DeclMod(Variability.CONSTANT,
     SymbolType.UNKNOWN), items=[DeclItm('a22', '')])),

    ('species a', Decl(mod=DeclMod(Variability.UNKNOWN,
     SymbolType.SPECIES), items=[DeclItm('a', '')])),

    ('formula a_ = 12.5\n', Decl(mod=DeclMod(Variability.UNKNOWN,
     SymbolType.PARAMETER), items=[DeclItm('a_', '12.5')])),

    ('compartment a', Decl(mod=DeclMod(Variability.UNKNOWN,
     SymbolType.COMPARTMENT), items=[DeclItm('a', '')])),

    ('const species foo;', Decl(mod=DeclMod(Variability.CONSTANT,
     SymbolType.SPECIES), items=[DeclItm('foo', '')])),

    ('var formula foo, b22=12.5,bar,c=-5e4* k - 2', Decl(mod=DeclMod(Variability.VARIABLE,
     SymbolType.PARAMETER), items=[DeclItm('foo', ''), DeclItm('b22', '12.5'), DeclItm('bar', ''),
     DeclItm('c', '-5e4 * k - 2')])),
])
def test_parse_declaration(code: str, expected: Decl):
    # TODO
    tree = parser.parse(code)
    assert len(tree.children) in (1, 2)
    stmt = tree.children[0]
    assert isinstance(stmt, SimpleStmt) and len(stmt.children) == 2

    declaration = stmt.children[0]
    assert isinstance(declaration, Declaration)

    mods = declaration.get_modifiers()
    assert mods.get_variab() == expected.mod.variab
    assert mods.get_type() == expected.mod.type

    items = declaration.get_items()
    assert [x.get_name_text() for x in items] == [x.name for x in expected.items]
    assert [formatted_code(x.get_value()) for x in items] == [x.value for x in expected.items]


def test_declaration_errors():
    # TODO
    pass


def test_parse_assignment():
    # TODO
    pass


def test_assignment_errors():
    # TODO
    pass


def test_parse_annotation():
    # TODO
    pass


# test statements without modules
def test_base_statements():
    # TODO
    pass


def test_base_errors():
    # TODO
    pass


def test_range():
    pass
