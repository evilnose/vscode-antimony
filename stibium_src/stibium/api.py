
from dataclasses import dataclass
from enum import Enum, auto
from typing import List
from lark.lexer import Token
from lark.tree import Tree
from stibium.ast import AntTreeAnalyzer, get_qname_at_position, handle_species_list
from stibium.parse import AntimonyParser
from stibium.types import Species, SrcPosition


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
        pstate = parser.get_state_at_position(None, text, position)
        basics = [AntCompletion(name, AntCompletionKind.TEXT) for name in analyzer.get_all_names()]

        # special rate law completions
        rate_laws = list()
        states = pstate.parse_conf.parse_table.states
        state_stack = pstate.state_stack
        value_stack = pstate.value_stack

        # check if we are at the rate law portion of a reaction
        if len(value_stack) >= 2:
            top = value_stack[-1]
            top2 = value_stack[-2]
            if (isinstance(top, Token) and top.value == ';' and isinstance(top2, Tree)
                and top2.data == 'products'):
                assert len(value_stack) >= 4 and value_stack[-4].data == 'reactants'

                reactants = handle_species_list(value_stack[-4]).logical_obj
                products = handle_species_list(value_stack[-2]).logical_obj
                snippet = self._mass_action_ratelaw(reactants, products)
                rate_laws.append(AntCompletion(snippet, AntCompletionKind.RATE_LAW))

        self._completions = basics + rate_laws
    
    def _mass_action_ratelaw(self, reactants: List[Species], products: List[Species]):
        toks = ['${1:k}']
        for species in reactants:
            toks.append(' * {}^{}'.format(species.name, species.stoich))

        for species in products:
            toks.append(' * {}^{}'.format(species.name, -species.stoich))
        
        return ''.join(toks)

    
    def completions(self):
        return self._completions

