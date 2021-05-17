'''Classes for working with and storing symbols.
'''
from .types import ObscuredDeclaration, ObscuredValue, SrcRange, SymbolType, IncompatibleType, ASTNode
from .utils import get_range

import abc
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional, Tuple, Union
from lark.lexer import Token

from lark.tree import Tree

'''Classes that represent contexts. TODO rename all these to Scope, b/c Scope is not the same thing as Context'''
class AbstractScope(abc.ABC):
    '''Should never be instantiated.'''
    pass


class BaseScope(AbstractScope):
    '''The highest-level context within a file, outside of any declared models.'''
    def __init__(self):
        pass

    def __eq__(self, other):
        if not isinstance(other, BaseScope):
            return NotImplemented
        
        return True

    def __hash__(self):
        return hash(('_base', ''))


class ModelScope(AbstractScope):
    '''The context for statements in declared models.'''
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, ModelScope):
            return NotImplemented
        
        return self.name == other.name

    def __hash__(self):
        return hash(('model', self.name))


class FunctionScope(AbstractScope):
    '''The context for statements in functions.'''
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, FunctionScope):
            return NotImplemented

        return self.name == other.name

    def __hash__(self):
        return hash(('function', self.name))


@dataclass
class QName:
    '''Represents a qualified name; i.e. a context and a name string.'''
    context: AbstractScope
    token: Token


class Symbol:
    '''A generic Symbol.

    TODO document what the tokens are
    Attributes:
        name:           The name of the symbol.
        typ:            The type of the symbol.
        type_token:     The exact AST token of the symbol.
        dcl_node:       The AST Node that represents the declaration statement of the symbol. May
                        be None if the symbol was not explicitly declared.
    '''

    name: str
    type: SymbolType
    type_token: Token
    decl_token: Optional[Token]
    decl_node: Optional[Tree]
    value_node: Optional[Tree]

    def __init__(self, name: str, typ: SymbolType, type_token: Token,
            decl_token: Token = None,
            decl_node: Tree = None,
            value_node: Tree = None):
        self.name = name
        self.type = typ
        self.type_token = type_token
        self.decl_token = decl_token
        self.decl_node = decl_node
        self.value_node = value_node

    def def_token(self):
        return self.decl_token or self.value_node or self.type_token

    def help_str(self):
        # TODO this is very basic right now. Need to create new Symbol classes for specific types
        # and get better data displayed here.
        return '({}) {}'.format(self.type, self.name)


class VarSymbol(Symbol):
    '''Represents a variable, rather than a function or model.
    
    TODO account for variability
    '''
    pass


# TODO allow the same context and name to map to multiple symbols, since antimony allows
# models and variables to have the same name
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

    def get(self, qname: QName) -> List[Symbol]:
        leaf_table = self._leaf_table(qname.context)
        name = str(qname.token)
        if name in leaf_table:
            return [leaf_table[name]]
        return []

    def insert(self, qname: QName, typ: SymbolType, decl_node: Tree = None,
               value_node: Tree = None):
        '''Insert a variable symbol into the symbol table.'''
        # TODO create more functions like insert_var(), insert_reaction(), insert_model() and
        # create more specific symbols. Need to store things like value for types like var.
        # Have an inner method that returns (added, [errors]). Update the value, etc. only if
        # successfully added.
        assert qname.token is not None
        issues = list()
        leaf_table = self._leaf_table(qname.context)
        name = str(qname.token)
        if name not in leaf_table:
            # TODO use a different Symbol class for other symbols
            sym = VarSymbol(name, typ, qname.token)
            leaf_table[name] = sym
        else:
            sym = leaf_table[name]
            old_type = sym.type

            if typ.derives_from(old_type):
                # new type is valid and narrower
                sym.type = typ
                sym.type_token = qname.token
            elif old_type.derives_from(typ):
                # legal, but useless information
                pass
            else:
                old_range = get_range(sym.type_token)
                new_range = get_range(qname.token)
                issues.append(IncompatibleType(old_type, old_range, typ, new_range))
                return issues

        # Override the declaration
        if decl_node is not None:
            decl_token = qname.token  # this is the declaration token
            if sym.decl_token is not None:
                old_range = get_range(sym.decl_token)
                new_range = get_range(decl_token)
                # Overriding previous declaration
                issues.append(ObscuredDeclaration(old_range, new_range, decl_token))
            sym.decl_node = decl_node
            sym.decl_token = decl_token

        if value_node is not None:
            value_token = qname.token  # this is the declaration token
            if sym.value_node is not None:
                old_range = get_range(sym.value_node)
                new_range = get_range(value_node)
                # Overriding previous declaration
                issues.append(ObscuredValue(old_range, new_range, value_token))
            sym.value_node = value_node

        return issues
