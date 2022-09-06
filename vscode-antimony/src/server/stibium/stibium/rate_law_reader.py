import os
import sys
import orjson
from collections import defaultdict
from server.stibium.stibium.analysis import AntTreeAnalyzer
from stibium.analysis import get_qname_at_position
from stibium.ant_types import SimpleStmt, Reaction
from stibium.parse import AntimonyParser
from stibium.types import SrcPosition


class RateLawReader:
    def __init__(self):
        self.substrate_product_dict = dict()
        
        f = open(os.path.join(sys.path[0], "db.json"), "r")
        data = f.read()
        rate_laws = orjson.loads(data)
        self.list_of_rate_laws = rate_laws['rateml']['listOfRateLaws']['law']
        self.rate_law_name_expression_dict = dict()
        for rate_law in self.list_of_rate_laws:
            substrate_product_string = ''
            substrate_product_string += rate_law['_numSubstrates'] + rate_law['_numProducts']
            constants = rate_law['listOfParameters']['parameter']
            self.rate_law_name_expression_dict[rate_law['_description']] = rate_law['_infixExpression']
            if substrate_product_string not in self.substrate_product_dict.keys():
                self.substrate_product_dict[substrate_product_string] = dict()
            self.substrate_product_dict[substrate_product_string][rate_law['_displayName']] = constants
    
    def get_rate_law(self, name: str):
        '''
        get the rate law expression with the given name
        '''
        if name in self.rate_law_name_expression_dict.keys():
            return self.rate_law_name_expression_dict[name]
        else:
            return '_error'
    
def substitute_rate_law(rate_law_str: str, substitute_dict: dict):
    keys = list(substitute_dict.keys())
    keys.sort(reverse=True)
    new_substitute_dict = dict()
    indicator = 0
    for key in keys:
        sub_key = 'zzz' + indicator + 'zzz'
        new_substitute_dict[sub_key] = substitute_dict[key]
        rate_law_str.replace(key, sub_key)
        indicator += 1
    for key in substitute_dict.keys():
        rate_law_str.replace(key, substitute_dict[key])
    return rate_law_str
    
def get_reaction_substrate_product_num(position: SrcPosition):
    '''
    get the number of substrates and products of a reaction given a position (the line that reaction is at)
    return in string form:
    for example, reaction with one substrate and two products will return '12'.
    '''
    # get_qname_at_position(position)
    pass
    
def get_reaction_substrate_product_num(text: str):
    '''
    get the number of substrates and products of a reaction given a string (the text of reaction)
    return in string form:
    for example, reaction with one substrate and two products will return '12'.
    '''
    parser = AntimonyParser()
    tree = parser.parse(text, recoverable=True)
    for child in reversed(tree):
        if isinstance(child, SimpleStmt):
            stmt = child.get_stmt()
            if stmt is None:
                continue
            if stmt.__class__.__name__ == 'Reaction':
                return stmt.get_reactant_product_num()
    return '_error'