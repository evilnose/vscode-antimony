"""Temporary test file; for convenience.

Definitely need to add a full suite of tests
"""

import os
import sys


# Temporary, before both packages are published
EXTENSION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(EXTENSION_ROOT, "stibium_src"))
sys.path.append(os.path.join(EXTENSION_ROOT, "stibium_server_src"))

from stibium.utils import formatted_code
from stibium.tree_builder import transform_tree
from stibium.types import SrcPosition
from stibium.parse import AntimonyParser
from .main import AntFile

from dataclasses import dataclass
from typing import List

FILE = ''';
@J0: 2C + 3B -> 2.5Deee; v
'''



# @dataclass
# class Species:
#     stoich: str
#     name: str


# @dataclass
# class Reaction:
#     reactants: List[Species]
#     products: List[Species]
#     rate_law: str

# @dataclass
# class Assignment:
#     name: str
#     value: str


def join_tokens(tokens):
    return ''.join(str(tok) for tok in tokens)

# doc = AntFile('hello', '2.5 A -> B;              ???? a= 5')
# print(doc.completions(SrcPosition(1, 13)))
# result = doc.parser.get_state_at_position('a^= 5', SrcPosition(1, 2))
# print(result.choices())
# doc = AntFile('hello', '''
# const species apple_1 = 10, apple_2
# banana: 2peach + 3orange -> 2.5 watermelon; aa

# badfruit = 5
# badfruit = 10
# badfruitother = 
# nothing

# i122 identity "http:identifiers.org/chebi/CHEBI:17234"

# ''')
# print(doc.get_errors())
parser = AntimonyParser()
FILE1 = '''
/* hi there


*/
const a
'''
tree = parser.parse(FILE1, False)
print(tree.children)

# print(formatted_code(tree) + 'DONE')

