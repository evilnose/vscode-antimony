

from typing import Tuple
from stibium.api import AntFile
from stibium.types import IncompatibleType, ObscuredValue, OverrodeValue, SpeciesUndefined, SrcPosition, SrcRange, UnexpectedEOFIssue, UnexpectedNewlineIssue, UnexpectedTokenIssue, UninitCompt

import pytest


@pytest.mark.parametrize('code', [
    ('''
const A = 10, A_2
formula B, CCC = 2 * (B - 3)
var $B = 2 * 5 * k, EF, IAC
J0: A + 3A_2 -> 2.5C; took

A_2 = 0
C = 0
took = 0
baggins = 5;;;

gamgee = 10
'''),
    ('formula a; compartment a'),  # compartment is a formula
    ('compartment a; formula a'),  # this is also fine; no conflict for now (might want to add warning later)
])
def test_no_issues(code):
    antfile = AntFile('', code)
    assert len(antfile.get_issues()) == 0


@pytest.mark.parametrize('code,range_,type_', [
    ('a=', (1, 2, 1, 3), UnexpectedEOFIssue),
    ('ae= \n', (1, 5, 2, 1), UnexpectedNewlineIssue),
    ('a=%', (1, 3, 1, 4), UnexpectedTokenIssue),
    ('a eee', (1, 3, 1, 6), UnexpectedTokenIssue),
])
def test_syntax_issue(code, range_: Tuple[int, int, int, int], type_):
    antfile = AntFile('', code)
    issues = antfile.get_issues()
    assert len(issues) == 1

    assert issues[0].range == SrcRange(SrcPosition(range_[0], range_[1]),
                                       SrcPosition(range_[2], range_[3]))
    assert isinstance(issues[0], type_)


def test_incompatible_declarations():
    antfile = AntFile('', 'species a1\ncompartment a1')
    issues = antfile.get_issues()
    assert len(issues) == 2

    assert isinstance(issues[0], IncompatibleType)
    assert isinstance(issues[1], IncompatibleType)
    assert issues[0].range == SrcRange(SrcPosition(2, 13), SrcPosition(2, 15))
    assert issues[1].range == SrcRange(SrcPosition(1, 9), SrcPosition(1, 11))


def test_incomp_incompatible():
    antfile = AntFile('', 'species a in a')
    issues = antfile.get_issues()
    assert len(issues) == 3
    
    assert isinstance(issues[0], UninitCompt)
    assert isinstance(issues[1], IncompatibleType)
    assert isinstance(issues[2], IncompatibleType)
    assert issues[0].range == SrcRange(SrcPosition(1, 14), SrcPosition(1, 15))
    assert issues[1].range == SrcRange(SrcPosition(1, 14), SrcPosition(1, 15))
    assert issues[2].range == SrcRange(SrcPosition(1, 9), SrcPosition(1, 10))


def test_reaction_incompat():
    antfile = AntFile('', 'J: A->B;1; J->A;1;\ncompartment J;')
    issues = antfile.get_issues()
    assert len(issues) == 8

    assert isinstance(issues[0], SpeciesUndefined)
    assert isinstance(issues[1], SpeciesUndefined)
    assert isinstance(issues[2], SpeciesUndefined)
    assert isinstance(issues[3], SpeciesUndefined)
    assert isinstance(issues[4], IncompatibleType)
    assert isinstance(issues[5], IncompatibleType)
    assert isinstance(issues[6], IncompatibleType)
    assert isinstance(issues[7], IncompatibleType)
    assert issues[0].range == SrcRange(SrcPosition(1, 4), SrcPosition(1, 5))
    assert issues[1].range == SrcRange(SrcPosition(1, 7), SrcPosition(1, 8))
    assert issues[2].range == SrcRange(SrcPosition(1, 12), SrcPosition(1, 13))
    assert issues[3].range == SrcRange(SrcPosition(1, 15), SrcPosition(1, 16))
    assert issues[4].range == SrcRange(SrcPosition(1, 12), SrcPosition(1, 13))
    assert issues[5].range == SrcRange(SrcPosition(1, 1), SrcPosition(1, 2))
    assert issues[6].range == SrcRange(SrcPosition(2, 13), SrcPosition(2, 14))
    assert issues[7].range == SrcRange(SrcPosition(1, 1), SrcPosition(1, 2))


def test_obscured_value():
    antfile = AntFile('', 'ke1 = 0; ke1 = 1; const ke1 = 2.1\nke2 = 6')
    issues = antfile.get_issues()
    # two issues, since the value is overwritten twice
    assert len(issues) == 4
    
    assert isinstance(issues[0], ObscuredValue)
    assert isinstance(issues[2], ObscuredValue)

    assert isinstance(issues[1], OverrodeValue)
    assert isinstance(issues[3], OverrodeValue)

    assert issues[0].old_range == issues[0].range
    # the range is that of the first full assignment
    assert issues[0].range == SrcRange(SrcPosition(1, 1), SrcPosition(1, 8))
    assert issues[0].new_range == SrcRange(SrcPosition(1, 10), SrcPosition(1, 17))

    # the range is that of the second full assignment, or the new_range of the first issue
    assert issues[1].old_range == issues[1].range == issues[0].new_range
    assert issues[2].new_range == SrcRange(SrcPosition(1, 25), SrcPosition(1, 34))
