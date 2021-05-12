import unittest

from stibium.parse import AntimonyParser
from stibium.utils import tree_str


parser = AntimonyParser()


# TODO add more tests as more syntax features are added
def test_tree_str():
    texts = ['a = 12.5 * b',
             'J0: A + 3B -> 10C + D; a * (4 + 3.332 ^ b);',
             '',
             '''
const species A = 10, A_2
formula B, CCC = 2 * (B - 3)
var B = 2 * 5 * k
J0: A + 3A_2 -> 2.5C; took

baggins = 5;;;

gamgee = 10

i122 identity "http://identifiers.org/chebi/CHEBI:17234"'''
             ]

    for text in texts:
        tree = parser.parse(text)
        # TODO incorporate parse(recoverblae=False) as well
        # add a newline since parse automatically appends a newline to the source
        assert text + '\n' == tree_str(tree)
    

def test_parse_reaction():
    # TODO
    pass
    

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
