'''Classes for working with and storing symbols.
'''
from stibium.ant_types import Name, TreeNode
from .types import ObscuredDeclaration, ObscuredValue, SrcRange, SymbolType, IncompatibleType, ASTNode
from .utils import get_range

import abc
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional, Tuple, Union
from lark.lexer import Token

from lark.tree import Tree

'''Classes that represent scopes. TODO rename all these to Scope, b/c Scope is not the same thing as scope'''
class AbstractScope(abc.ABC):
    '''Should never be instantiated.'''
    pass


class BaseScope(AbstractScope):
    '''The highest-level scope within a file, outside of any declared models.'''
    def __init__(self):
        pass

    def __eq__(self, other):
        if not isinstance(other, BaseScope):
            return NotImplemented
        
        return True

    def __hash__(self):
        return hash(('_base', ''))


class ModelScope(AbstractScope):
    '''The scope for statements in declared models.'''
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, ModelScope):
            return NotImplemented
        
        return self.name == other.name

    def __hash__(self):
        return hash(('model', self.name))


class FunctionScope(AbstractScope):
    '''The scope for statements in functions.'''
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
    '''Represents a qualified name; i.e. a scope and a name string.'''
    scope: AbstractScope
    name: Name


class Symbol:
    '''A generic Symbol.

    TODO document what the tokens are
    Attributes:
        name:           The name of the symbol.
        typ:            The type of the symbol.
        type_name:     The exact AST token of the symbol.
        dcl_node:       The AST Node that represents the declaration statement of the symbol. May
                        be None if the symbol was not explicitly declared.
    '''

    name: str
    type: SymbolType
    type_name: Name
    decl_name: Optional[Name]
    decl_node: Optional[TreeNode]
    value_node: Optional[TreeNode]

    def __init__(self, name: str, typ: SymbolType, type_name: Name,
            decl_name: Name = None,
            decl_node: TreeNode = None,
            value_node: TreeNode = None):
        self.name = name
        self.type = typ
        self.type_name = type_name
        self.decl_name = decl_name
        self.decl_node = decl_node
        self.value_node = value_node

    def def_name(self):
        '''Return the Name that should be considered as the definition'''
        return self.decl_name or self.value_node or self.type_name

    def help_str(self):
        # TODO this is very basic right now. Need to create new Symbol classes for specific types
        # and get better data displayed here.
        return '({}) {}'.format(self.type, self.name)


class VarSymbol(Symbol):
    '''Represents a variable, rather than a function or model.
    
    TODO account for variability
    '''
    pass


# TODO allow the same scope and name to map to multiple symbols, since antimony allows
# models and variables to have the same name
class SymbolTable:
    # In the future, maybe use a tree-like data structure? Probably not necessary though - Gary.
    table: DefaultDict[AbstractScope, Dict[str, Symbol]]

    def __init__(self):
        ''''''
        self.table = defaultdict(dict)

    def _leaf_table(self, scope: AbstractScope):
        return self.table[scope]

    def get_all_names(self):
        '''Get all the unique names in the table (outside of scope) '''
        names = set()
        for leaf_table in self.table.values():
            names |= leaf_table.keys()
        return list(names)

    def get_unique_name(self, scope: AbstractScope, prefix: str):
        '''Obtain a unique name under the scope by trying successively larger number suffixes.'''
        leaf_table = self._leaf_table(scope)
        i = 0
        while True:
            name = '{}{}'.format(prefix, i)
            if name not in leaf_table:
                break
            i += 1

    def get(self, qname: QName) -> List[Symbol]:
        leaf_table = self._leaf_table(qname.scope)
        name = qname.name.text
        if name in leaf_table:
            return [leaf_table[name]]
        return []

    def insert(self, qname: QName, typ: SymbolType, decl_node: TreeNode = None,
               value_node: TreeNode = None):
        '''Insert a variable symbol into the symbol table.'''
        # TODO create more functions like insert_var(), insert_reaction(), insert_model() and
        # create more specific symbols. Need to store things like value for types like var.
        # Have an inner method that returns (added, [errors]). Update the value, etc. only if
        # successfully added.
        assert qname.name is not None
        issues = list()
        leaf_table = self._leaf_table(qname.scope)
        name = qname.name.text
        if name not in leaf_table:
            # TODO use a different Symbol class for other symbols
            sym = VarSymbol(name, typ, qname.name)
            leaf_table[name] = sym
        else:
            sym = leaf_table[name]
            old_type = sym.type

            if typ.derives_from(old_type):
                # new type is valid and narrower
                sym.type = typ
                sym.type_name = qname.name
            elif old_type.derives_from(typ):
                # legal, but useless information
                pass
            else:
                old_range = sym.type_name.range
                new_range = qname.name.range
                issues.append(IncompatibleType(old_type, old_range, typ, new_range))
                return issues

        # Override the declaration
        if decl_node is not None:
            decl_name = qname.name
            if sym.decl_name is not None:
                old_range = sym.decl_name.range
                new_range = decl_name.range
                # Overriding previous declaration
                issues.append(ObscuredDeclaration(old_range, new_range, decl_name.text))
            sym.decl_node = decl_node
            sym.decl_name = decl_name

        if value_node is not None:
            value_name = qname.name
            if sym.value_node is not None:
                old_range = sym.value_node.range
                new_range = value_name.range
                # Overriding previous declaration
                issues.append(ObscuredValue(old_range, new_range, value_name.text))
            sym.value_node = value_node

        return issues
