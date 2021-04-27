import abc
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import DefaultDict, Dict, Optional, Tuple, Union
from lark.lexer import Token

from lark.tree import Tree
from pygls.types import Position, Range

from classes import SymbolType, IncompatibleTypeError, ASTNode
from utils import get_range


class AbstractContext(abc.ABC):
    pass


class BaseModelContext(AbstractContext):
    def __init__(self):
        pass

    def __eq__(self, other):
        if not isinstance(other, BaseModelContext):
            return NotImplemented
        
        return True

    def __hash__(self):
        return hash(('_base', ''))


class ModelContext(AbstractContext):
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, ModelContext):
            return NotImplemented
        
        return self.name == other.name

    def __hash__(self):
        return hash(('model', self.name))


class FunctionContext(AbstractContext):
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, FunctionContext):
            return NotImplemented

        return self.name == other.name

    def __hash__(self):
        return hash(('function', self.name))


class Symbol:
    def __init__(self, name: str, typ: SymbolType, src_token: Token, src_node: Optional[ASTNode]):
        '''Creates a generic Symbol.

        Args:
            name:       The name of the symbol.
            typ:        The type of the symbol.
            src_node:   The AST Node that contains the full information concerning the symbol.
            src_token:  The exact AST token of the symbol.
        '''
        self.name = name
        self.type = typ
        self.src_token = src_token
        self.src_node = src_node


class VarSymbol(Symbol):
    '''Represents a variable, rather than a function or model.
    
    TODO account for variability
    '''
    decl_node: Optional[ASTNode]
    def __init__(self, name: str, typ: SymbolType, src_token: Token, src_node: Optional[ASTNode]):
        super().__init__(name, typ, src_token, src_node)
        self.src_node = src_node


class SymbolTable:
    # In the future, maybe use a tree-like data structure? Probably not necessary though - Gary.
    table: DefaultDict[AbstractContext, Dict[str, Symbol]]

    def __init__(self):
        self.table = defaultdict(dict)

    def _leaf_table(self, context: AbstractContext):
        return self.table[context]

    def get_all_names(self):
        names = set()
        for leaf_table in self.table.values():
            names |= leaf_table.keys()
        return names

    def get_unique_name(self, context: AbstractContext, prefix: str):
        '''Obtain a unique name under the context by trying successively larger number suffixes.'''
        leaf_table = self._leaf_table(context)
        i = 0
        while True:
            name = '{}{}'.format(prefix, i)
            if name not in leaf_table:
                break
            i += 1

    def insert_var(self, context: AbstractContext, name: str, typ: SymbolType, src_tok: Token,
                   src_node: ASTNode = None):
        leaf_table = self._leaf_table(context)
        if name not in leaf_table:
            sym = VarSymbol(name, typ, src_tok, src_node)
            leaf_table[name] = sym
        else:
            sym = leaf_table[name]
            old_type = sym.type
            if typ.derives_from(old_type):
                # new type is valid and narrower
                sym.type = typ
                sym.src_token = src_tok
            elif old_type.derives_from(typ):
                # legal, but useless information
                pass
            else:
                # TODO errored
                old_range = get_range(sym.src_token)
                new_range = get_range(src_tok)
                # TODO
                error = IncompatibleTypeError(old_type, old_range, typ, new_range)
                return [error]

            if sym.src_node is None:
                sym.src_node = src_node

        return []
