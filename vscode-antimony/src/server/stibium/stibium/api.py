
from dataclasses import dataclass
from enum import Enum, auto
import logging
from typing import List, Optional, cast
from lark.lexer import Token
from lark.tree import Tree
from stibium.ant_types import NameMaybeIn, Number, Reaction, ReactionName, SpeciesList
from stibium.analysis import AntTreeAnalyzer, get_qname_at_position
from stibium.parse import AntimonyParser
from stibium.symbols import QName, BaseScope
from stibium.tree_builder import Species, transform_tree
from stibium.types import Issue, SrcLocation, SrcPosition
from stibium.utils import to_uri

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
        puppet = parser.get_puppet_at_position(text, position)
        basics = [AntCompletion(name, AntCompletionKind.TEXT) for name in analyzer.get_all_names()]
        imports = [AntCompletion(name, AntCompletionKind.TEXT) for name in analyzer.get_all_import_names()]

        # special rate law completions
        rate_laws = list()

        choices = puppet.choices()
        reaction: Optional[Reaction] = None
        # try to construct a reaction
        if 'NUMBER' in choices:
            rxn_puppet = puppet.copy()
            rxn_puppet.feed_token(Token('NUMBER', 0))  # type: ignore
            if 'NEWLINE' in rxn_puppet.choices():
                rxn_puppet.feed_token(Token('NEWLINE', ''))  # type: ignore

                vstack = rxn_puppet.parser_state.value_stack
                if len(vstack) >= 2:
                    maybe_reaction = vstack[-2]
                    if isinstance(maybe_reaction, Tree) and maybe_reaction.data == 'reaction':
                        # we're at the start of the rate law of a reaction!
                        reaction = cast(Reaction, transform_tree(maybe_reaction))
                        assert isinstance(reaction, Reaction)

        # construct rate law completion if we're at the start of the rate law portion of a reaction
        # Note that if the rate law of a reaction is not merely a number, it means we might be in
        # a situation like 'A -> B;  1 * ', where the rate law is already being populated. For
        # now, we don't do any completion in this case.
        if reaction is not None and isinstance(reaction.get_rate_law(), Number):
            # use reaction's name or generate one if it is anonymous
            reaction_name = reaction.get_name_text() or analyzer.get_unique_name('J')
            snippet = self._mass_action_ratelaw(reaction_name,
                                                reaction.get_reactants(),
                                                reaction.get_products(),
                                                reaction.is_reversible())
            rate_laws.append(AntCompletion(snippet, AntCompletionKind.RATE_LAW))

        self._completions = basics + imports + rate_laws

    def _mass_action_ratelaw(self, name: str, reactants: List[Species], products: List[Species],
                             reversible: bool):

        def species_list_str(species_list: List[Species]):
            if not species_list:
                return ''
            toks = list()
            for species in species_list:
                tok = species.get_name().text
                if species.get_stoich() != 1:
                    # add exponent
                    tok += '^{:g}'.format(species.get_stoich())
                toks.append(tok)
            return ' * ' + ' * '.join(toks)

        # snippet is of the format '${1:placeholder} ... ${2:placeholder} ...'. We want to use
        # Python formatting to interpolate the reaction name into this getting something like
        # '${1:k_J0}', but Python format treats '{}' as interpolation, so we need to use two
        # brackets '{{}}' to escape that.
        snippet = f'${{1:k_f_{name}}}' + species_list_str(reactants)

        if reversible:
            # if reactants_str is nonempty, then that means there is already ${1:k_f..} in the
            # snippet. We set the second parameter to {2:k_b..} in this case, as it is the
            # second move target for tab.
            snippet += ' - ${{2:k_b_{name}}}{products}'.format(name=name,
                products=species_list_str(products))

        return snippet

    def completions(self):
        return self._completions


# Holds information pertaining to one Antimony document
# TODO move this to stibium.api
class AntFile:
    '''Interface for an Antimony source file and contains useful methods.'''

    def __init__(self, path: str, text: str):
        self.path = path
        self.text = text
        self.parser = AntimonyParser()
        self.tree = self.parser.parse(text, recoverable=True)
        self.analyzer = AntTreeAnalyzer(self.tree, self.path)

    def symbols_at(self, position: SrcPosition):
        '''Return (symbols, range) where symbols is the list of symbols that the token at
        position may resolve to, and range is the range of the token under the position.

        TODO make a copy
        TODO no need to return range now
        '''
        assert isinstance(position, SrcPosition)
        qname = get_qname_at_position(self.tree, position)
        if qname is None:
            return [], None
        assert qname.name is not None
        resolved = self.analyzer.resolve_qname(qname)
        if len(resolved) == 0:
            resolved = self.analyzer.resolve_import_qname(qname)
        if len(resolved) == 0:
            qname.scope = BaseScope()
            resolved = self.analyzer.resolve_qname(qname)
        if len(resolved) == 0:
            qname.scope = BaseScope()
            resolved = self.analyzer.resolve_import_qname(qname)
        return resolved, qname.name.range

    def goto(self, position: SrcPosition):
        symbols, range_ = self.symbols_at(position)
        if not symbols and position.column - 1 >= 0:
            position = SrcPosition(position.line, position.column - 1)
            symbols, range_ = self.symbols_at(position)
            if not symbols:
                position = SrcPosition(position.line, position.column + 1)
                symbols, range_ = self.symbols_at(position)
        if not symbols:
            return [], range_

        return [SrcLocation(
            to_uri(self.path),  # TODO: might be other files when we add cross-file functionalities
            sym.def_name().range,
        ) for sym in symbols], range_

    def get_issues(self) -> List[Issue]:
        return self.analyzer.get_issues()

    def save_checkpoint(self, tree) -> bool:
        '''Returns whether we should save the state of the parser (i.e. in a ParserPuppet).

        Basically returns whether the rule that was just parsed is a complete rule, i.e. a statement
        or a model-end. This way, if we encounter an error later, we can restore the puppet to
        this complete state, find the next newline or semicolon, and continue parsing (having
        skipped the errored part).
        '''
        if tree.data in ('reaction', 'assignment', 'declaration', 'annotation', 'model'):
            return True

        return False

    def completions(self, position: SrcPosition):
        completer = Completer(self.analyzer, self.parser, self.text, position)
        return completer.completions()

    def get_annotations(self, qname: QName):
        # TODO HACK this isn't very elegant -- no encapsulation
        cur_annot = self.analyzer.table.get(qname)[0].annotations
        import_annot = self.analyzer.import_table.get(qname)[0].annotations
        return cur_annot + import_annot
