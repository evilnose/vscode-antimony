
from dataclasses import dataclass
from enum import Enum, auto
from typing import List
from lark.lexer import Token
from lark.tree import Tree
from stibium.ant_types import SpeciesList
from stibium.ast import AntTreeAnalyzer, get_qname_at_position
from stibium.parse import AntimonyParser
from stibium.tree_builder import Species, transform_tree
from stibium.types import SrcPosition


class AntCompletionKind(Enum):
    TEXT = auto()
    RATE_LAW = auto()


@dataclass(frozen=True)
class AntCompletion:
    text: str
    kind: AntCompletionKind


class Completer:
    def __init__(self, analyzer: AntTreeAnalyzer, parser: AntimonyParser, text: str,
                 position: SrcPosition):
        # TODO refactor: instead of passing analyzer and text as separate values, create a class
        # to hold the current inference state. analyzer would be passed a state variable, and it
        # would update it (e.g. with symbol information)
        # TODO maybe move the actual completion code out from the constructor to completions()?
        '''NOTE
        Right now completion makes use of only the parser state (stacks) at the completion
        position. This won't be sufficient for more sophisticated completion. Below is a TODO list
        
        * If completion is done in the middle of a token (e.g. gluco<-- completion here), we would
        need to find the previous token (beware of edge case at beginning of file), do completion
        after that, and filter to get completions that begin with the token prefix.
        * Get the scope of the token. It's probably possible to do this with just the parser
        stacks, but I think it'd be easier with 
        * possible optimization, see get_state_and_position()
        
        '''

        # TODO fix: what if there is no token at the given position?
        # qname = get_qname_at_position(analyzer.root, position)
        # pstate = parser.get_state_at_position(qname.token, text, position)

        # TODO replace None with qname.token after get_qname_at_position is fixed
        pstate = parser.get_state_at_position(text, position)
        basics = [AntCompletion(name, AntCompletionKind.TEXT) for name in analyzer.get_all_names()]

        # special rate law completions
        rate_laws = list()
        states = pstate.parse_conf.parse_table.states
        state_stack = pstate.state_stack
        value_stack = pstate.value_stack

        # check if we are at the rate law portion of a reaction
        if len(value_stack) >= 4:
            top = value_stack[-1]
            top2 = value_stack[-2]
            top4 = value_stack[-4]
            if (isinstance(top, Token) and top.value == ';' and isinstance(top2, Tree)
                and top2.data == 'species_list' and top4.data == 'species_list'):
                assert len(value_stack) >= 4 and value_stack[-4].data == 'species_list'

                reactant_list = transform_tree(value_stack[-4])
                product_list = transform_tree(value_stack[-2])
                assert isinstance(reactant_list, SpeciesList)
                assert isinstance(product_list, SpeciesList)
                reversible = value_stack[-3].value == '=>'
                snippet = self._mass_action_ratelaw(reactant_list.get_all_species(),
                                                    product_list.get_all_species(),
                                                    reversible)
                rate_laws.append(AntCompletion(snippet, AntCompletionKind.RATE_LAW))

        self._completions = basics + rate_laws
    
    def _mass_action_ratelaw(self, reactants: List[Species], products: List[Species], reversible: bool):

        def species_list_str(species_list: List[Species]):
            toks = list()
            for species in species_list:
                toks.append('{}^{}'.format(species.get_name().text, species.get_stoich()))
            return ' * '.join(toks)
        
        snippet = '${1:k} * ' + species_list_str(reactants)

        if reversible:
            snippet += ' - ' + species_list_str(products)

        return snippet

    
    def completions(self):
        return self._completions

