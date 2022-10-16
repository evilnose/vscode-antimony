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
    print(ant_file.analyzer.table.get_all_qnames())
    # Test first assignment within base file
    assignment = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(3, 9), SrcPosition(3, 10)), text='b')))[0].value_node.unit.get_name().text
    assert assign_vals[1] == assignment, "Incorrect unit"

    # Test second assignment from imported file
    assignment = ant_file.analyzer.table.get(QName(BaseScope(), name=Name(range=SrcRange(SrcPosition(4, 1), SrcPosition(4, 2)), text='a')))[0].value_node.unit.get_name().text
    assert assign_vals[0] == assignment, "Incorrect unit"


