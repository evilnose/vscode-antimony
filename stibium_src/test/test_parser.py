from typing import List, Optional, Tuple
from lark.tree import Tree
from stibium.ant_types import FileNode

from stibium.parse import AntimonyParser
from stibium.utils import formatted_code


parser = AntimonyParser()


# TODO add more tests as more syntax features are added
def test_formatted_code():
    texts = ['a = 12.5 * b',
             'J0: A + 3B -> 10C + $D; a * (4 + 3.332 ^ b);',
             '',
             '''
const A = 10, A_2
formula B, CCC = 2 * (B - 3)
var $B = 2 * 5 * k, EF, IAC
J0: A + 3A_2 -> 2.5C; took

baggins = 5;;;

gamgee = 10

i122 identity "http://identifiers.org/chebi/CHEBI:17234"'''
             ]

    for text in texts:
        tree = parser.parse(text, recoverable=False)  # tree without error recovery
        other_tree = parser.parse(text)
        assert tree == other_tree, text
        assert text == formatted_code(tree), text
    

def test_parse_end_marker():
    '''Ensure this handles end marker well.'''
    tree = parser.parse('foo = 3.5', recoverable=False)
    assert len(tree.children) == 1
    tree = parser.parse('foo = 3.5;', recoverable=False)
    assert len(tree.children) == 1


# TODO Refactor this later once I implement transformer
# def validate_reaction(suite, , reactants: List[Tuple[float, str]],
#                       products: List[Tuple[float, str]]):
#     assert isinstance(suite, Tree)
#     assert len(suite.children) == 2

#     reaction = suite.children[0]

#     assert isinstance(reaction, Tree)
#     assert len(reaction.children) == 7

#     if name:
#         maybein = resolve_maybein(reaction.children[0])
#         assert str(maybein.name_item.name_tok) == name
#     else:
#         assert reaction.children[0] is None
    

def test_parse_reaction():
    text = 'J0: A -> B; 2 * k;'
    tree = parser.parse(text, recoverable=False)

    assert len(tree.children) == 1
    # TODO
    # validate_reaction(tree.children[0], 'J0', [(1, 'A')], [(1, 'B')])
    

def test_reaction_errors():
    # TODO
    pass
    

def test_parse_declaration():
    # TODO
    pass
    

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
