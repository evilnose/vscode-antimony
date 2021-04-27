'''Classes for working with and storing symbols.
'''
import abc
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import DefaultDict, Dict, Optional, Tuple, Union
from lark.lexer import Token

from lark.tree import Tree
from pygls.types import Position, Range

from classes import ObscuredDeclaration, SymbolType, IncompatibleType, ASTNode
from utils import get_range


'''Classes that represent contexts. TODO do we need treelike contexts?'''
class AbstractContext(abc.ABC):
    '''Should never be instantiated.'''
    pass


class BaseContext(AbstractContext):
    '''The highest-level context within a file, outside of any declared models.'''
    def __init__(self):
        pass

    def __eq__(self, other):
        if not isinstance(other, BaseContext):
            return NotImplemented
        
        return True

    def __hash__(self):
        return hash(('_base', ''))


class ModelContext(AbstractContext):
    '''The context for statements in declared models.'''
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, ModelContext):
            return NotImplemented
        
        return self.name == other.name

    def __hash__(self):
        return hash(('model', self.name))


class FunctionContext(AbstractContext):
    '''The context for statements in functions.'''
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, FunctionContext):
            return NotImplemented

        return self.name == other.name

    def __hash__(self):
        return hash(('function', self.name))


class Symbol:
    name: str
    typ: SymbolType
    src_token: Token
    src_node: Optional[ASTNode]
    '''A generic Symbol.

    Attributes:
        name:       The name of the symbol.
        typ:        The type of the symbol.
        src_token:  The exact AST token of the symbol.
        src_node:   The AST Node that represents the declaration statement of the symbol. May
                    be None if the symbol was not explicitly declared.
    '''
    def __init__(self, name: str, typ: SymbolType, src_token: Token, src_node: Optional[ASTNode]):
        self.name = name
        self.type = typ
        self.src_token = src_token
        self.src_node = src_node


class VarSymbol(Symbol):
    '''Represents a variable, rather than a function or model.
    
    TODO account for variability
    '''
    pass


class SymbolTable:
    # In the future, maybe use a tree-like data structure? Probably not necessary though - Gary.
    table: DefaultDict[AbstractContext, Dict[str, Symbol]]

    def __init__(self):
        ''''''
        self.table = defaultdict(dict)

    def _leaf_table(self, context: AbstractContext):
        return self.table[context]

    def get_all_names(self):
        '''Get all the unique names in the table (outside of context) '''
        names = set()
        for leaf_table in self.table.values():
            names |= leaf_table.keys()
        return list(names)

    def get_unique_name(self, context: AbstractContext, prefix: str):
        '''Obtain a unique name under the context by trying successively larger number suffixes.'''
        leaf_table = self._leaf_table(context)
        i = 0
        while True:
            name = '{}{}'.format(prefix, i)
            if name not in leaf_table:
                break
            i += 1

    def insert(self, context: AbstractContext, name: str, typ: SymbolType, src_tok: Token,
                   src_node: ASTNode = None):
        '''Insert a variable symbol into the symbol table.'''
        issues = list()
        try:
            leaf_table = self._leaf_table(context)
            if name not in leaf_table:
                # TODO use a different Symbol class for other symbols
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
                    old_range = get_range(sym.src_token)
                    new_range = get_range(src_tok)
                    issues.append(IncompatibleType(old_type, old_range, typ, new_range))
                    return

                if src_node is not None:
                    if sym.src_node is not None:
                        old_range = get_range(sym.src_node)
                        new_range = get_range(src_node)
                        # Overriding previous declaration
                        issues.append(ObscuredDeclaration(old_range, new_range, name))
                    sym.src_node = src_node
        finally:
            return issues
