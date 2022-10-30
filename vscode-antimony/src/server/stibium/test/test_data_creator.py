import os
import re
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
from stibium.api import AntFile
from stibium.parse import AntimonyParser
from pygls.workspace import Document
import json
parser = AntimonyParser()
directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-data")

def creator():
    data = {}
    for file_name in os.listdir(directory):
        f = os.path.join(directory, file_name)
        doc = Document(os.path.abspath(f))
        ant_file = AntFile(doc.path, doc.source)
        actual_str = parser.get_parse_tree_str(ant_file.text, recoverable=True)
        data[os.path.splitext(file_name)[0]] = actual_str
    print(str(data))

if __name__ == "__main__":
    creator()
        
        