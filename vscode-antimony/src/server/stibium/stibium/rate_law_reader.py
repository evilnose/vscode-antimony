import os
import sys
import orjson
from stibium.ant_types import SimpleStmt, Reaction
from stibium.parse import AntimonyParser


class RateLawReader:
    def __init__(self, text: str):
        '''
        :param text: The reaction string
        self.reactant_product_num = '_error' the text given is not a reaction
        '''
        self.relevant_rate_laws = list()
        parser = AntimonyParser()
        tree = parser.parse(text, recoverable=True)
        self.reactant_product_num = '_error'
        self.reaction = None
        for child in reversed(tree):
            if isinstance(child, SimpleStmt):
                stmt = child.get_stmt()
                if stmt is None:
                    continue
                if stmt.__class__.__name__ == 'Reaction':
                    self.reactant_product_num = stmt.get_reactant_product_num()
                    self.reaction = stmt
                    break
        if self.reaction is not None:
            f = open(os.path.join(sys.path[0], "db.json"), "r")
            data = f.read()
            rate_laws = orjson.loads(data)
            for rate_law in rate_laws['rateml']['listOfRateLaws']['law']:
                substrate_product_num = ''
                substrate_product_num += rate_law['_numSubstrates'] + rate_law['_numProducts']
                
                constants: list = rate_law['listOfParameters']['parameter']
                if substrate_product_num == self.reactant_product_num:
                    expression = substitute_rate_law_participants(rate_law['_infixExpression'], self.reaction)
                    self.relevant_rate_laws.append({
                        'name': rate_law['_displayName'],
                        'orig_expr': rate_law['_infixExpression'],
                        'expression': expression,
                        'constants': constants,
                    })

    def no_rate_law_check(self):
        '''
        check if there is no rate law exist
        '''
        assert isinstance(self.reaction, Reaction)
        if self.reaction.get_rate_law():
            return '_error'
        return 'correct'
    
def substitute_rate_law_participants(rate_law_str: str, reaction: Reaction):
    '''
    substitute a raw rate law string with a reaction
    '''
    indicator = 1
    for substrate in reaction.get_reactants():
        rate_law_str.replace('___S' + indicator + '___', substrate.get_name_text())
        indicator += 1
    indicator = 1
    for product in reaction.get_products():
        rate_law_str.replace('___P' + indicator + '___', product.get_name_text())
        indicator += 1
    return rate_law_str