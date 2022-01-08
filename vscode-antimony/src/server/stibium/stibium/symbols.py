'''Classes for working with and storing symbols.
'''
import logging
from stibium.ant_types import Annotation, Name, TreeNode
from .types import ObscuredValueCompartment, RedefinedFunction, OverrodeValue, ObscuredDeclaration, ObscuredValue, SrcRange, SymbolType, IncompatibleType
from .ant_types import Declaration, VariableIn, Function, DeclItem, Assignment, ModularModel, Number, ModularModelCall

import abc
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional, Set, Tuple, Union
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

class ModularModelScope(AbstractScope):
    '''The scope for statements in declared models.'''
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, ModularModelScope):
            return NotImplemented
        
        return self.name == other.name

    def __hash__(self):
        return hash(('modular_model', self.name))


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
        type_name:     The exact analysis token of the symbol.
        dcl_node:       The analysis Node that represents the declaration statement of the symbol. May
                        be None if the symbol was not explicitly declared.
    '''

    name: str
    type: SymbolType
    type_name: Name
    decl_name: Optional[Name]
    decl_node: Optional[TreeNode]
    value_node: Optional[TreeNode]
    annotations: List[Annotation]

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
        self.annotations = list()

    def def_name(self):
        '''Return the Name that should be considered as the definition'''
        return self.decl_name or self.value_node or self.type_name

    def help_str(self):
        if isinstance(self, MModelSymbol):
            name = self.name
            ret = '```\n{}'.format(name) + "("
            for index, param in enumerate(self.parameters):
                if not param:
                    ret += ")"
                    return ret
                type = param[0].type
                ret += str(type) + ": " + param[0].name
                if index != len(self.parameters) - 1:
                    ret += ", "
            ret += ")```"
        elif isinstance(self, FuncSymbol):
            name = self.name
            ret = '```\n{}'.format(name) + "("
            for index, param in enumerate(self.parameters):
                ret += param[0].name
                if index != len(self.parameters) - 1:
                    ret += ", "
            ret += ")```"
        elif self.value_node is not None and self.value_node.get_value() is not None \
            and isinstance(self.value_node.get_value(), Number):
            if isinstance(self.value_node, Assignment) and self.value_node.get_type() is not None:
                ret = '```\n({}) {}\n{}\n```'.format(
                    self.type, self.name, 
                    "Initialized Value: " + self.value_node.get_value().text + " (" + 
                    self.value_node.get_type().get_str() + ")")
            elif isinstance(self.value_node, DeclItem) and self.value_node.get_decl_assignment().get_type() is not None:
                ret = '```\n({}) {}\n{}\n```'.format(
                    self.type, self.name, 
                    "Initialized Value: " + self.value_node.get_value().text + " (" + 
                    self.value_node.get_decl_assignment().get_type().get_str() + ")")
            else:
                ret = '```\n({}) {}\n{}\n```'.format(
                    self.type, self.name, 
                    "Initialized Value: " + self.value_node.get_value().text)
        else:
            ret = '```\n({}) {}\n```'.format(self.type, self.name)
    
        if self.annotations:
            # add the first annotation
            ret += '\n\n***\n\n{}'.format(self.annotations[0].get_uri())
        return ret


class VarSymbol(Symbol):
    '''Represents a variable, rather than a function or model.
    
    TODO account for variability
    '''

class FuncSymbol(Symbol):
    '''
    Symbol for func
    '''
    parameters: List[VarSymbol]

    def __init__(self, name: str, typ: SymbolType, type_name: Name,
            parameters):
        Symbol.__init__(self, name, typ, type_name)
        self.parameters = parameters

class MModelSymbol(Symbol):
    '''
    Symbol for modular model
    '''
    parameters: List[VarSymbol]

    def __init__(self, name: str, typ: SymbolType, type_name: Name,
            parameters):
        Symbol.__init__(self, name, typ, type_name)
        self.parameters = parameters

# TODO allow the same scope and name to map to multiple symbols, since antimony allows
# models and variables to have the same name
class SymbolTable:
    # In the future, maybe use a tree-like data structure? Probably not necessary though - Gary.
    _table: DefaultDict[AbstractScope, Dict[str, Symbol]]
    _qnames: List[QName]

    def __init__(self):
        self._table = defaultdict(dict)
        self._error = list()
        self._warning = list()
        self._qnames = list()

    def _leaf_table(self, scope: AbstractScope):
        return self._table[scope]

    @property
    def error(self):
        return self._error

    @property
    def warning(self):
        return self._warning

    def get_all_names(self):
        '''Get all the unique names in the table as a set (outside of scope) '''
        names = set()
        for leaf_table in self._table.values():
            names |= leaf_table.keys()
        return names

    def get_all_qnames(self):
        '''Get all the unique names in the table as a set (outside of scope) '''
        return self._qnames

    def get_unique_name(self, prefix: str, scope: AbstractScope = None) -> str:
        '''Obtain a unique name under the scope by trying successively larger number suffixes.
        
        If scope is None, then find a name unique in every scope.
        '''
        if scope is None:
            all_names = self.get_all_names()

            i = 0
            while True:
                name = '{}{}'.format(prefix, i)
                if name not in all_names:
                    break
                i += 1
        else:
            leaf_table = self._leaf_table(scope)
            i = 0
            while True:
                name = '{}{}'.format(prefix, i)
                if name not in leaf_table:
                    break
                i += 1
        return name

    def get(self, qname: QName) -> List[Symbol]:
        leaf_table = self._leaf_table(qname.scope)
        name = qname.name.text
        if isinstance(name, str) and name in leaf_table:
            return [leaf_table[name]]
        else:
            return []
    
    def insert_function_holder(self, function, scope):
        leaf_table = self._leaf_table(scope)
        sym = FuncSymbol(function.name, function.type, function.type_name, parameters=function.parameters)
        leaf_table[function.name] = sym

    def insert_function(self, qname: QName, typ: SymbolType, parameters, decl_node: TreeNode = None,
               value_node: TreeNode = None):
        assert qname.name is not None
        self._qnames.append(qname)
        leaf_table = self._leaf_table(qname.scope)
        name = qname.name.get_name().text
        if name not in leaf_table:
            sym = FuncSymbol(name, typ, qname.name.get_name(), parameters=parameters)
            leaf_table[name] = sym
        else:
            # variable already exists
            sym = leaf_table[name]
            old_type = sym.type
            if typ.derives_from(old_type):
                old_range = sym.type_name.range
                # new type is valid and narrower
                sym.type = typ
                sym.type_name = qname.name
                # error
                new_range = qname.name.get_name().range
                self._error.append(RedefinedFunction(new_range, name, old_range))
                self._error.append(RedefinedFunction(old_range, name, new_range))
            else:
                old_range = sym.type_name.range
                new_range = qname.name.get_name().range
                self._error.append(IncompatibleType(old_type, old_range, typ, new_range))
                self._error.append(IncompatibleType(old_type, new_range, typ, old_range))
        

    def insert_mmodel(self, qname: QName, typ: SymbolType, parameters, decl_node: TreeNode = None,
               value_node: TreeNode = None):
        assert qname.name is not None
        self._qnames.append(qname)
        name = qname.name.get_name().text
        sym = MModelSymbol(name, type, qname.name, parameters=parameters)
        leaf_table = self._leaf_table(qname.scope)
        leaf_table[name] = sym

    def insert(self, qname: QName, typ: SymbolType, decl_node: TreeNode = None,
               value_node: TreeNode = None):
        '''Insert a variable symbol into the symbol table.'''
        # TODO create more functions like insert_var(), insert_reaction(), insert_model() and
        # create more specific symbols. Need to store things like value for types like var.
        # Have an inner method that returns (added, [errors]). Update the value, etc. only if
        # successfully added.
        assert qname.name is not None
        self._qnames.append(qname)
        leaf_table = self._leaf_table(qname.scope)
        name = qname.name.text
        if name not in leaf_table:
            # first time parsing, insert directly in the table
            sym = VarSymbol(name, typ, qname.name)
            leaf_table[name] = sym
        else:
            # variable already exists
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
                if value_node is not None:
                    self._error.append(IncompatibleType(old_type, old_range, typ, value_node.range))
                    self._error.append(IncompatibleType(old_type, value_node.range, typ, old_range))
                else:
                    self._error.append(IncompatibleType(old_type, old_range, typ, new_range))
                    self._error.append(IncompatibleType(old_type, new_range, typ, old_range))
                return

        # warning: overriding previous assignment
        if value_node is not None:
            value_name = qname.name
            if sym.value_node is not None:
                old_range = sym.value_node.range
                new_range = value_node.range
                # Overriding previous declaration
                self._warning.append(ObscuredValue(old_range, new_range, value_name.text))
                self._warning.append(OverrodeValue(new_range, old_range, value_name.text))
            sym.value_node = value_node
        elif decl_node is not None:
            decl_name = qname.name
            if sym.decl_node is not None and (type(decl_node) != Declaration or decl_node.get_modifiers is None):
                old_range = sym.decl_node.range
                new_range = decl_node.range
                # Overriding previous declaration
                if isinstance(decl_node, VariableIn):
                    self._warning.append(ObscuredValueCompartment(old_range, new_range, decl_name.text))
                    self._warning.append(ObscuredValueCompartment(new_range, old_range, decl_name.text))
                else:
                    self._warning.append(ObscuredValue(old_range, new_range, decl_name.text))
                    self._warning.append(OverrodeValue(new_range, old_range, decl_name.text))
            sym.decl_node = decl_node
            sym.decl_name = decl_name


    def insert_annotation(self, qname: QName, node: Annotation):
        leaf_table = self._leaf_table(qname.scope)
        name = qname.name.text
        if name not in leaf_table:
            sym = VarSymbol(name, SymbolType.Unknown, qname.name)
            leaf_table[name] = sym
        else:
            sym = leaf_table[name]
        sym.annotations.append(node)
