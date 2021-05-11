import unittest

from stibium.parse import AntimonyParser
from stibium.utils import tree_str


parser = AntimonyParser()


# TODO use pytest
# TODO list the tests you want to do
def test_tree_str():
    texts = ['a = 12.5 * b',
             'J0: A + 3B -> 10C + D; a * (4 + 3.332 ^ b);',
             '',
             '''
             '''
             ]

    for text in texts:
        tree = parser.parse(text)
        # add a newline since parse automatically appends a newline to the source
        assert text + '\n' == tree_str(tree)
