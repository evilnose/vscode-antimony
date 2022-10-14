import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from stibium.symbols import BaseScope, QName
from stibium.api import AntFile
from stibium.parse import AntimonyParser

from pygls.workspace import Document

import pytest

parser = AntimonyParser()
directory = os.path.join(os.path.dirname(os.path.abspath(__file__)))

@pytest.mark.parametrize('file_name, parse_tree_str', [
    ('base', "Tree('root', [Tree('simple_stmt', [Tree('import', [Token('IMPORT', 'import'), Token('ESCAPED_STRING', '\"import.ant\"')]), Token('NEWLINE', '\\n\\n')]), Tree('simple_stmt', [Tree('assignment', [Tree('namemaybein', [Tree('var_name', [None, Token('NAME', 'b')]), None]), Token('EQUAL', '='), Token('NUMBER', '4')]), Token('NEWLINE', '')])])"),
])
def test_import(file_name, parse_tree_str):
    file = os.path.join(directory, file_name + '.ant')
    doc = Document(os.path.abspath(file))
    ant_file = AntFile(doc.path, doc.source)
    issues = ant_file.get_issues()
    error_count = 0
    for issue in issues:
        print(issue)
        if str(issue.severity.__str__()) == 'IssueSeverity.Error':
            error_count += 1
    assert error_count == 0, "Import unsuccessful"
    if error_count == 0:
        actual_str = parser.get_parse_tree_str(ant_file.text)
        print(actual_str)
        assert parse_tree_str == actual_str, "Incorrect contents imported"