import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from stibium.ant_types import Import, Name
from stibium.types import SrcPosition, SrcRange
from stibium.symbols import BaseScope, QName
from stibium.api import AntFile
from stibium.parse import AntimonyParser

from pygls.workspace import Document

import pytest

parser = AntimonyParser()
directory = os.path.join(os.path.dirname(os.path.abspath(__file__)))



@pytest.mark.parametrize("file_name, parse_tree_str", [
    ("base", "Tree('root', [Tree('simple_stmt', [Tree('import', [Token('IMPORT', 'import'), Token('ESCAPED_STRING', '\"import.ant\"')]), Token('NEWLINE', '\\n\\n')]), Tree('simple_stmt', [Tree('assignment', [Tree('namemaybein', [Tree('var_name', [None, Token('NAME', 'test')]), None]), Token('EQUAL', '='), Token('NUMBER', '4')]), Token('NEWLINE', '')])])"),
])
def test_import(file_name, parse_tree_str):
    file = os.path.join(directory, file_name + ".ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 0, "Import unsuccessful"
    actual_str = parser.get_parse_tree_str(ant_file.text)
    assert parse_tree_str == actual_str, "Incorrect contents imported"


@pytest.mark.parametrize("assign_vals", [
    (["10", "4", "4 mass"]),
])
def test_assign(assign_vals):
    file = os.path.join(directory, "assign.ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 0, "Import unsuccessful"

    stmt = ant_file.tree.children[0].get_stmt()
    assert isinstance(stmt, Import)

    # Test first assignment within base file
    assignment= ant_file.analyzer.table.get(QName(BaseScope(), Name(range=SrcRange(SrcPosition(3, 5), SrcPosition(3, 6)), text='a')))[0].value_node
    cur_val = assignment.get_value().text
    assert assign_vals[0] == cur_val, "Incorrect assignment"

    # Test second assignment from imported file
    assignment = ant_file.analyzer.table.get(QName(BaseScope(), Name(range=SrcRange(SrcPosition(3, 9), SrcPosition(3, 10)), text='b')))[0].value_node
    cur_val = assignment.get_value().text
    assert assign_vals[1] == cur_val, "Incorrect assignment"

    # Test third assignmetn from imported file with unit in base file
    assignment = ant_file.analyzer.table.get(QName(BaseScope(), Name(range=SrcRange(SrcPosition(3, 9), SrcPosition(3, 10)), text='b')))[0].value_node
    cur_val = assignment.get_value().text
    cur_val +=  " " + assignment.get_type().get_name_text()
    assert assign_vals[2] == cur_val, "Incorrect assignment"


@pytest.mark.parametrize("assign_vals", [
    (["\"in base file\"", "\"not imported\""]),
])
def test_is_assign(assign_vals):
    file = os.path.join(directory, "assign.ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 0, "Import unsuccessful"

    stmt = ant_file.tree.children[0].get_stmt()
    assert isinstance(stmt, Import)

    # Test first assignment within base file
    assignment = ant_file.analyzer.table.get(QName(BaseScope(), Name(range=SrcRange(SrcPosition(3, 9), SrcPosition(3, 10)), text='b')))[0].display_name
    assert assign_vals[1] == assignment, "Incorrect display name"

    # Test second assignment from imported file
    assignment = ant_file.analyzer.table.get(QName(BaseScope(), Name(range=SrcRange(SrcPosition(4, 1), SrcPosition(4, 2)), text='a')))[0].display_name
    assert assign_vals[0] == assignment, "Incorrect display name"


@pytest.mark.parametrize("assign_vals", [
    (["vol", "mass"])
])
def test_unit_assign(assign_vals):
    file = os.path.join(directory, "assign.ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 0, "Import unsuccessful"

    stmt = ant_file.tree.children[0].get_stmt()
    assert isinstance(stmt, Import)

    # Test first assignment within base file
    assignment = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(3, 9), SrcPosition(3, 10)), text='b')))[0].value_node.unit.get_name().text
    assert assign_vals[1] == assignment, "Incorrect unit"

    # Test second assignment from imported file
    assignment = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(4, 1), SrcPosition(4, 2)), text='a')))[0].value_node.unit.get_name().text
    assert assign_vals[0] == assignment, "Incorrect unit"


@pytest.mark.parametrize("reactions", [
    (["a", "b", "kfc"])
])
def test_reaction(reactions):
    file = os.path.join(directory, "reaction.ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 0, "Import unsuccessful"

    stmt = ant_file.tree.children[0].get_stmt()
    assert isinstance(stmt, Import)

    # Test first reaction within base file
    reaction = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(6, 1), SrcPosition(6, 3)), text='J4')))[0].decl_node
    reactants = reaction.get_reactants()
    products = reaction.get_products()
    constants = reaction.get_rate_law()
    assert reactions[0] == reactants[0].get_name_text(), "Incorrect species"
    assert reactions[1] == reactants[1].get_name_text(), "Incorrect species"
    assert reactions[1] == products[0].get_name_text(), "Incorrect species"
    assert reactions[2] == constants.get_name_text(), "Incorrect constant"

    # Test second reaction from imported file
    reaction = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(7, 1), SrcPosition(7, 3)), text='J0')))[0].decl_node
    reactants = reaction.get_reactants()
    products = reaction.get_products()
    constants = reaction.get_rate_law()
    assert reactions[0] == reactants[0].get_name_text(), "Incorrect species"
    assert reactions[1] == products[0].get_name_text(), "Incorrect species"
    assert reactions[2] == constants.get_name_text(), "Incorrect constant"


def test_mmodel_call():
    file = os.path.join(directory, "mmodel_calls.ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 1, "Import unsuccessful"

    # Test for duplicate mmodel call
    error_msg = "The modular model call 'MC' has been duplicated, please make sure there is only one modular model call of this name"
    assert error_msg == issues[0].message, "Incorrect error encountered"

    stmt = ant_file.tree.children[0].get_stmt()
    assert isinstance(stmt, Import)

    # Test imported mmodel call
    call = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(11, 1), SrcPosition(11, 4)), text='MC2')))[0].value_node
    assert call.get_mmodel_name_str() == "foo"


def test_func_call():
    file = os.path.join(directory, "func_calls.ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 0, "Import unsuccessful"

    stmt = ant_file.tree.children[0].get_stmt()
    assert isinstance(stmt, Import)

    # Test first function call within base file
    call = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(8, 1), SrcPosition(8, 3)), text='FC')))[0].value_node
    assert call.get_function_name_str() == "constant"

    # Test second function call from imported file
    call = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(9, 1), SrcPosition(9, 4)), text='FC2')))[0].value_node
    assert call.get_function_name_str() == "varsum"


def test_annot():
    file = os.path.join(directory, "annot.ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 0, "Import unsuccessful"

    stmt = ant_file.tree.children[0].get_stmt()
    assert isinstance(stmt, Import)

    # Test number of annotations for variable in current and imported files
    annot_list = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(4, 1), SrcPosition(4, 2)), text='b')))[0].annotations
    assert len(annot_list) == 2

    # Test number of annotations for variable in current file
    annot_list = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(3, 1), SrcPosition(3, 2)), text='a')))[0].annotations
    assert len(annot_list) == 1


def test_mmodel():
    file = os.path.join(directory, "mmodel.ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 1, "Import unsuccessful"

    # Test for duplicate mmodel
    error_msg = "Model 'foo' is already defined, or there is a circular import"
    assert error_msg == issues[0].message, "Incorrect error encountered"


def test_func():
    file = os.path.join(directory, "func.ant")
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        if str(issue.severity.__str__()) == "IssueSeverity.Error":
            error_count += 1
    assert error_count == 1, "Import unsuccessful"

    # Test for duplicate function
    error_msg = "Function 'varsum' is already defined"
    assert error_msg == issues[0].message, "Incorrect error encountered"