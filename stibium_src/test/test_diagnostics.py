

from stibium.api import AntFile
from stibium.types import IncompatibleType, ObscuredValue, SrcPosition, SrcRange

import pytest


@pytest.mark.parametrize('code', [
    ('''
const A = 10, A_2
formula B, CCC = 2 * (B - 3)
var $B = 2 * 5 * k, EF, IAC
J0: A + 3A_2 -> 2.5C; took

baggins = 5;;;

gamgee = 10

i122 identity "http://identifiers.org/chebi/CHEBI:17234"'''),
    ('formula a; compartment a'),  # compartment is a formula
    ('compartment a; formula a'),  # this is also fine; no conflict for now (might want to add warning later)
])
def test_no_issues(code):
    antfile = AntFile('', code)
    assert len(antfile.get_issues()) == 0


def test_incompatible_declarations():
    antfile = AntFile('', 'species a1\ncompartment a1')
    issues = antfile.get_issues()
    assert len(issues) == 1
    issue = issues[0]

    assert isinstance(issue, IncompatibleType)
    assert issue.range == SrcRange(SrcPosition(2, 13), SrcPosition(2, 15))


def test_incomp_incompatible():
    antfile = AntFile('', 'species a in a')
    issues = antfile.get_issues()
    assert len(issues) == 1
    issue = issues[0]

    assert isinstance(issue, IncompatibleType)
    assert issue.range == SrcRange(SrcPosition(1, 14), SrcPosition(1, 15))


def test_reaction_incompat():
    antfile = AntFile('', 'J: A->B;1; J->A;1;\ncompartment J;')
    issues = antfile.get_issues()
    assert len(issues) == 2

    assert isinstance(issues[0], IncompatibleType)
    assert isinstance(issues[1], IncompatibleType)
    assert issues[0].range == SrcRange(SrcPosition(1, 12), SrcPosition(1, 13))
    assert issues[1].range == SrcRange(SrcPosition(2, 13), SrcPosition(2, 14))


def test_obscured_value():
    antfile = AntFile('', 'ke1 = 0; ke1 = 1; const ke1 = 2.1\nke2 = 6')
    issues = antfile.get_issues()
    # two issues, since the value is overwritten twice
    assert len(issues) == 2
    assert isinstance(issues[0], ObscuredValue)
    assert isinstance(issues[1], ObscuredValue)

    assert issues[0].old_range == issues[0].range
    # the range is that of the first full assignment
    assert issues[0].range == SrcRange(SrcPosition(1, 1), SrcPosition(1, 8))
    assert issues[0].new_range == SrcRange(SrcPosition(1, 10), SrcPosition(1, 17))

    # the range is that of the second full assignment, or the new_range of the first issue
    assert issues[1].old_range == issues[1].range == issues[0].new_range
    assert issues[1].new_range == SrcRange(SrcPosition(1, 25), SrcPosition(1, 34))
