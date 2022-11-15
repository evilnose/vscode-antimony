'''Tests concerning auto-completion. Note that completion is still very primitive right now and
does not vary based on cursor context (with the exception of rate law). So I expect this file to
be heavily modified in the future.
'''

from typing import List
from stibium.api import AntCompletion, AntCompletionKind, AntFile
from stibium.parse import AntimonyParser
from stibium.types import SrcPosition

import pytest


def test_basic_completion():
    # For now we're not filtering the completed names based on the prefix
    code = '''
const species apple_1 = 10, apple_2
banana: 2peach + 3orange => 2.5 watermelon; k * peach^2.0 * orange^3.0

badfruit = 5
badfruit = 10
badfruitother = 
nothing
i122 = 0

    '''
    antfile = AntFile('', code)
    position = SrcPosition(4, 1)
    actual = antfile.completions(position)
    actual.sort(key=lambda x: x.text)

    names = ['apple_1', 'apple_2', 'banana', 'peach', 'orange', 'watermelon', 'k', 'badfruit',
             'i122']
    expected = [AntCompletion(name, AntCompletionKind.TEXT) for name in sorted(names)]

    assert expected == actual


@pytest.mark.parametrize('code,pos,text_comps,snippet_comps', [
    ('2A -> B;  ', SrcPosition(1, 9), ['A', 'B'], []),
    # space after
    (' A -> B;  ', SrcPosition(1, 10), ['A', 'B'], []),
    # garbage tokens afterwards
    ('A => B;      *&&^(', SrcPosition(1, 9), [], ['${1:k_f_J0} * A']),
    # statement afterwards
    ('A => B;      ; k = 10.5', SrcPosition(1, 9), ['A', 'B','k'], ['${1:k_f_J0} * A']),
    # reaction name and two reactants
    ('J12: 2A +   3B => B;  ', SrcPosition(1, 21), ['A', 'B', 'J12'], []),
    # reversible
    ('J3: 2A +   3 B -> B + 4.5C; 1             ', SrcPosition(1, 29), ['A', 'B', 'C', 'J3'],
       ['${1:k_f_J3} * A^2 * B^3 - ${2:k_b_J3} * B * C^4.5']),
    # generate unique name
    ('J0: 1A => B;1\nA=>B;     \nJ1: C=>D;1', SrcPosition(2, 7), ['A', 'B', 'C', 'D', 'J0', 'J1'], ['${1:k_f_J2} * A']),
    # no reactants
    ('J3:          => B + 4.5C;             ', SrcPosition(1, 30), ['B', 'C', 'J3'], []),
    # no reactants (reversible)
    ('J3:          -> B;           ', SrcPosition(1, 30), ['B', 'J3'], []),
    # no products (no completions for that for now)
    ('J3:       A   =>         ;             ', SrcPosition(1, 30), ['A', 'J3'], []),
    # wrong place (name)
    ('J3:    A    =>    B    ;             ', SrcPosition(1, 2), ['A', 'B', 'J3'], []),
    # wrong place (reactants)
    ('J3:    A    =>    B    ;             ', SrcPosition(1, 5), ['A', 'B', 'J3'], []),
    # wrong place (products)
    ('J3:    A    =>    B    ;             ', SrcPosition(1, 17), ['A', 'B', 'J3'], []),
    # wrong place (after existing rate law)
    ('J3:    A    ->    B    ;  1   ;         ', SrcPosition(1, 28), ['A', 'B', 'J3'], []),
    # wrong place (after reaction)
    ('J3:    A    ->    B    ;  1   ;         ', SrcPosition(1, 33), ['A', 'B', 'J3'], []),
    # wrong place (no semicolon)
    ('J3:    A    ->    B                     ', SrcPosition(1, 33), [], []),
])
def test_mass_action(code: str, pos: SrcPosition, text_comps: List[str], snippet_comps: List[str]):
    antfile = AntFile('', code)
    actual = antfile.completions(pos)
    actual_texts = [x.text for x in actual if x.kind == AntCompletionKind.TEXT]
    actual_texts.sort()
    actual_snippets = [x.text for x in actual if x.kind == AntCompletionKind.RATE_LAW]
    actual_snippets.sort()

    text_comps.sort()
    snippet_comps.sort()

    assert actual_texts == text_comps
    assert actual_snippets == snippet_comps

