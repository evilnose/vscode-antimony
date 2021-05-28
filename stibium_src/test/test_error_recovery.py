from stibium.ant_types import Assignment, DeclModifiers, ErrorNode, ErrorToken, NameMaybeIn, Number, Reaction, SimpleStmt, TypeModifier, VarModifier
from stibium.parse import AntimonyParser
from stibium.utils import formatted_code

import pytest


parser = AntimonyParser()


@pytest.mark.parametrize('code', [
    ('?$a= 3'),
    ('=$a  =3')
])
def test_leading_tokens(code):
    tree = parser.parse(code, recoverable=True)
    assert isinstance(tree.children[0], ErrorToken)
    assert isinstance(tree.children[1], SimpleStmt)

    assignment = tree.children[1].get_stmt()
    assert isinstance(assignment, Assignment)
    assert assignment.get_name_text() == 'a'

    assert formatted_code(assignment) == '$a = 3'


def test_partial_stmt():
    tree = parser.parse('a =?', recoverable=True)
    assert isinstance(tree.children[0], ErrorNode)
    assert isinstance(tree.children[1], ErrorToken)

    # make sure '=' is parsed as an operator
    assert formatted_code(tree.children[0]) == 'a = '
    # note at this point there is no ambiguity that 'a =' is the start of an assignment rule, so
    # 'a' should be parsed as a NameMaybeIn 
    assert isinstance(tree.children[0].children[0], NameMaybeIn)


def test_almost_full_stmt():
    '''Here there is still an error node, because a = 5 itself is not a full statement.'''
    tree = parser.parse('a = 5*3?', recoverable=True)
    assert isinstance(tree.children[0], ErrorNode)
    assert isinstance(tree.children[1], ErrorToken)

    assert formatted_code(tree.children[0]) == 'a = 5 * 3'
    # ErrorNode should have five children, since we're not certain at this point if the rate rule
    # has ended
    assert len(tree.children[0].children) == 5


def test_full_stmt():
    '''Here there should not be an error node, since the statement was terminated.'''
    tree = parser.parse('a = 5*3;?', recoverable=True)
    assert isinstance(tree.children[0], SimpleStmt)
    assert isinstance(tree.children[0].children[0], Assignment)
    assert isinstance(tree.children[1], ErrorToken)


def test_full_stmt_1():
    tree = parser.parse('J0: A -> B; 20^k\n=', recoverable=True)
    assert isinstance(tree.children[0], SimpleStmt)
    assert isinstance(tree.children[0].children[0], Reaction)
    assert isinstance(tree.children[1], ErrorToken)


def test_recovered():
    '''Make sure the statement after the error is fine'''
    tree = parser.parse('J0: A -> const\n  cee =  12', recoverable=True)
    assert isinstance(tree.children[0], ErrorNode)
    assert isinstance(tree.children[1], ErrorToken)  # 'const'
    assert isinstance(tree.children[2], SimpleStmt)  # empty stmt between const and newline
    assert isinstance(tree.children[3], SimpleStmt)
    stmt = tree.children[3].get_stmt()
    assert isinstance(stmt, Assignment) and formatted_code(stmt) == 'cee = 12'


def test_unexpected_eof():
    tree = parser.parse('a = ', recoverable=True)
    assert len(tree.children) == 1
    assert isinstance(tree.children[0], ErrorNode)
    # EOF is *not* added as an ErrorToken since we normally don't see EOF anyway


def test_unexpected_newline():
    # same thing with comments
    tree = parser.parse('a = \n;', recoverable=True)
    assert len(tree.children) == 4

    # did not expect this newline
    assert isinstance(tree.children[0], ErrorNode)
    assert isinstance(tree.children[1], ErrorToken) and tree.children[1].text == '\n'
    assert isinstance(tree.children[2], SimpleStmt)  # empty stmt between \n and ;
    assert isinstance(tree.children[3], SimpleStmt)  # empty stmt between ; and EOF


def test_sandwich():
    '''Error token sandwiched between (possibly partial) statements'''
    tree = parser.parse('var compartment ^ c = 5', recoverable=True)
    assert len(tree.children) == 3
    assert isinstance(tree.children[0], ErrorNode)
    assert isinstance(tree.children[0].children[0], VarModifier)
    assert isinstance(tree.children[0].children[1], TypeModifier)

    assert isinstance(tree.children[1], ErrorToken)

    assert isinstance(tree.children[2], SimpleStmt)
    assert isinstance(tree.children[2].get_stmt(), Assignment)


def test_wrong_name():
    tree = parser.parse('compartment compartment a = 5', recoverable=True)
    # the second compartment should be discarded as an ErrorToken, so we should get an assignment

    assert isinstance(tree.children[0], ErrorNode)
    assert isinstance(tree.children[1], ErrorToken)
    assert isinstance(tree.children[2], SimpleStmt)

    assert formatted_code(tree.children[2]) == 'a = 5'


def test_multiple_tokens():
    tree = parser.parse('$$==]$%', recoverable=True)

    assert len(tree.children) == 7
    assert isinstance(tree.children[0], ErrorNode)  # $
    assert isinstance(tree.children[1], ErrorToken)  # $
    assert isinstance(tree.children[2], ErrorToken)  # =
    assert isinstance(tree.children[3], ErrorToken)  # =
    assert isinstance(tree.children[4], ErrorToken)  # ]
    assert isinstance(tree.children[5], ErrorNode)  # $
    assert isinstance(tree.children[6], ErrorToken)  # %


def test_unmatched_quote():
    '''We try to match string literal but fail. Thus, '"' and 'fefeeeee' are treated as their own
    tokens.
    '''
    tree = parser.parse('a identity "fefeeeeee\nc=5', recoverable=True)
    assert len(tree.children) == 5
    assert isinstance(tree.children[0], ErrorNode)
    assert isinstance(tree.children[1], ErrorToken)  # don't expect "
    assert isinstance(tree.children[2], ErrorNode)  # expected fefeeeee but failed immediately
    assert isinstance(tree.children[3], ErrorToken)  # don't expect \n right after Name
    assert isinstance(tree.children[4], SimpleStmt)  # full assignment here
