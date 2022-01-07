
import logging
from stibium.ant_types import VariableIn, NameMaybeIn, FunctionCall, ModularModelCall, Number, Operator, VarName, DeclItem, UnitDeclaration, Parameters, ModularModel, Function, SimpleStmtList, End, Keyword, Annotation, ArithmeticExpr, Assignment, Declaration, ErrorNode, ErrorToken, FileNode, Function, InComp, LeafNode, Model, Name, Reaction, SimpleStmt, TreeNode, TrunkNode
from .types import SpeciesUndefined, IncorrectParamNum, ParamIncorrectType, UninitFunction, UninitMModel, UninitCompt, UnusedParameter, RefUndefined, ASTNode, Issue, SymbolType, SyntaxErrorIssue, UnexpectedEOFIssue, UnexpectedNewlineIssue, UnexpectedTokenIssue, Variability, SrcPosition
from .symbols import AbstractScope, BaseScope, FunctionScope, ModelScope, QName, SymbolTable, ModularModelScope

from dataclasses import dataclass
from typing import Any, List, Optional, Set, cast
from itertools import chain
from lark.lexer import Token
from lark.tree import Tree


def get_qname_at_position(root: FileNode, pos: SrcPosition) -> Optional[QName]:
    '''Returns (context, token) the given position. `token` may be None if not found.
    '''
    def within_range(pos: SrcPosition, node: TreeNode):
        return pos >= node.range.start and pos < node.range.end

    node: TreeNode = root
    model: Optional[Name] = None
    func: Optional[Name] = None
    mmodel: Optional[Name] = None
    
    while not isinstance(node, LeafNode):
        if isinstance(node, Model):
            assert model is None
            model = node.get_name()
        elif isinstance(node, Function):
            assert func is None
            func = node.get_name()
        elif isinstance(node, ModularModel):
            assert mmodel is None
            mmodel = node.get_name()

        for child in node.children:
            if child is None:
                continue

            if within_range(pos, child):
                node = child
                break
        else:
            # Didn't find it
            return None

    # can't have nested models/functions
    assert not (model is not None and func is not None)
    if model:
        scope = ModelScope(str(model))
    elif func:
        scope = FunctionScope(str(func))
    elif mmodel:
        scope = ModularModelScope(str(mmodel))
    else:
        scope = BaseScope()
    return QName(scope, node)


class AntTreeAnalyzer:
    def __init__(self, root: FileNode):
        self.table = SymbolTable()
        self.root = root
        base_scope = BaseScope()
        for child in root.children:
            if isinstance(child, ErrorToken):
                continue
            if isinstance(child, ErrorNode):
                continue
            if isinstance(child, Model):
                scope = ModelScope(str(child.get_name()))
                for cchild in child.children:
                    if isinstance(cchild, ErrorToken):
                        continue
                    if isinstance(cchild, ErrorNode):
                        continue
                    if isinstance(cchild, SimpleStmtList):
                        for st in cchild.children:
                            if isinstance(st, ErrorToken):
                                continue
                            if isinstance(st, ErrorNode):
                                continue
                            stmt = st.get_stmt()
                            if stmt is None:
                                continue
                            {
                                'Reaction': self.handle_reaction,
                                'Assignment': self.handle_assignment,
                                'Declaration': self.handle_declaration,
                                'Annotation': self.handle_annotation,
                                'UnitDeclaration': self.handle_unit_declaration,
                                'UnitAssignment' : self.handle_unit_assignment,
                                'ModularModelCall' : self.handle_mmodel_call,
                                'FunctionCall' : self.handle_function_call,
                                'VariableIn' : self.handle_variable_in,
                            }[stmt.__class__.__name__](scope, stmt)
                            self.handle_child_incomp(scope, stmt)
            if isinstance(child, ModularModel):
                scope = ModularModelScope(str(child.get_name()))
                for cchild in child.children:
                    if isinstance(cchild, ErrorToken):
                        continue
                    if isinstance(cchild, ErrorNode):
                        continue
                    if isinstance(cchild, SimpleStmtList):
                        for st in cchild.children:
                            if isinstance(st, ErrorToken):
                                continue
                            if isinstance(st, ErrorNode):
                                continue
                            stmt = st.get_stmt()
                            if stmt is None:
                                continue
                            {
                                'Reaction': self.handle_reaction,
                                'Assignment': self.handle_assignment,
                                'Declaration': self.handle_declaration,
                                'Annotation': self.handle_annotation,
                                'UnitDeclaration': self.handle_unit_declaration,
                                'UnitAssignment' : self.handle_unit_assignment,
                                'ModularModelCall' : self.handle_mmodel_call,
                                'FunctionCall' : self.handle_function_call,
                                'VariableIn' : self.handle_variable_in,
                            }[stmt.__class__.__name__](scope, stmt)
                            self.handle_child_incomp(scope, stmt)
                    if isinstance(cchild, Parameters):
                        self.handle_parameters(scope, cchild)
                self.handle_mmodel(child)
            if isinstance(child, Function):
                scope = FunctionScope(str(child.get_name()))
                self.handle_function(child)
                for cchild in child.children:
                    if isinstance(cchild, ErrorToken):
                        continue
                    if isinstance(cchild, ErrorNode):
                        continue
                    if isinstance(cchild, ArithmeticExpr):
                        self.handle_arith_expr(scope, cchild)
                    if isinstance(cchild, Parameters):
                        self.handle_parameters(scope, cchild)
            if isinstance(child, SimpleStmt):
                if isinstance(child, ErrorToken):
                    continue
                if isinstance(child, ErrorNode):
                    continue
                stmt = child.get_stmt()
                if stmt is None:
                    continue
                {
                    'Reaction': self.handle_reaction,
                    'Assignment': self.handle_assignment,
                    'Declaration': self.handle_declaration,
                    'Annotation': self.handle_annotation,
                    'UnitDeclaration': self.handle_unit_declaration,
                    'UnitAssignment' : self.handle_unit_assignment,
                    'ModularModelCall' : self.handle_mmodel_call,
                    'FunctionCall' : self.handle_function_call,
                    'VariableIn' : self.handle_variable_in,
                }[stmt.__class__.__name__](base_scope, stmt)
                self.handle_child_incomp(base_scope, stmt)
        
        # get list of errors from the symbol table
        self.error = self.table.error
        # get list of warnings
        self.warning = self.table.warning
        self.check_parse_tree(self.root, BaseScope())

    def resolve_qname(self, qname: QName):
        return self.table.get(qname)

    def get_all_names(self) -> Set[str]:
        # TODO temporary method to satisfy auto-completion
        return self.table.get_all_names()

    def get_issues(self) -> List[Issue]:
        return (self.warning + self.error).copy()
    
    def check_parse_tree(self, root, scope):
        # 1. check rate laws:
        #   1.1 referencing undefined parameters
        #   1.2 unused parameters in function/mmodel
        # 2. syntax issue when parsing the grammar
        #   Note: this could be due to partially implemented grammar at this moment
        # 3. referencing undefined compartment
        # 4. calling undefined function/modular model
        # 5. check parameters
        lines = set()
        for node in root.children:
            if node is None:
                continue
            if type(node) == Model:
                self.check_parse_tree(node.get_stmt_list(), ModelScope(str(node.get_name())))
            if type(node) == Function:
                #   1.1 referencing undefined parameters
                #   1.2 unused parameters in function
                self.check_parse_tree_function(node, FunctionScope(str(node.get_name())))
            if type(node) == ModularModel:
                #   1.1 referencing undefined parameters
                #   1.2 unused parameters in mmodel
                self.check_parse_tree_mmodel(node, ModularModelScope(str(node.get_name())))
            # 2. syntax issue when parsing the grammar
            self.check_syntax_issues(node)

            # 3. 
            if type(node) == SimpleStmt and (type(node.get_stmt()) == Reaction or \
                                               type(node.get_stmt()) == Assignment or \
                                               type(node.get_stmt()) == Declaration or \
                                               type(node.get_stmt()) == ModularModelCall or \
                                               type(node.get_stmt()) == FunctionCall or \
                                               type(node.get_stmt()) == VariableIn):
                if type(node.get_stmt()) == Declaration:
                    for item in node.get_stmt().get_items():
                        maybein = item.get_maybein()
                        if maybein is not None and maybein.is_in_comp():
                            comp = maybein.get_comp()
                            compt = self.table.get(QName(scope, comp.get_name()))
                            if compt[0].value_node is None:
                                # 3. add warning
                                self.warning.append(UninitCompt(comp.get_name().range, comp.get_name_text()))
                elif type(node.get_stmt()) == VariableIn:
                    comp = node.get_stmt().get_incomp().get_comp()
                    compt = self.table.get(QName(scope, comp.get_name()))
                    if compt[0].value_node is None:
                        # 3. add warning
                        self.warning.append(UninitCompt(comp.get_name().range, comp.get_name_text()))
                    # also check if the parameter is defined or not
                    param_name = node.get_stmt().get_name()
                    matched_param = self.table.get(QName(scope, param_name.get_name()))
                    if matched_param[0].value_node is None:
                        self.error.append(RefUndefined(param_name.get_name().range, param_name.get_name_text()))
                else:
                    maybein = node.get_stmt().get_maybein()
                    if maybein is not None and maybein.is_in_comp():
                        comp = maybein.get_comp()
                        compt = self.table.get(QName(scope, comp.get_name()))
                        if compt[0].value_node is None:
                            # 3. add warning
                            self.warning.append(UninitCompt(comp.get_name().range, comp.get_name_text()))
            #   1.1 referencing undefined parameters
            if type(node) == SimpleStmt and type(node.get_stmt()) == Reaction:
                reaction = node.get_stmt()
                rate_law = reaction.get_rate_law()
                self.check_rate_law(rate_law, scope)
                # check if all species have been initialized
                species_list = []
                for species in reaction.get_reactants():
                    species_list.append(species)
                for species in reaction.get_products():
                    species_list.append(species)
                for species in species_list:
                    species_name = species.get_name()
                    matched_species = self.table.get(QName(scope, species_name))
                    if matched_species[0].value_node is None:
                        self.warning.append(SpeciesUndefined(species.range, species_name))
            # 4. 
            if type(node) == SimpleStmt and type(node.get_stmt()) == ModularModelCall:
                mmodel_name = node.get_stmt().get_mmodel_name()
                mmodel = self.table.get(QName(BaseScope(), mmodel_name))
                if len(mmodel) == 0:
                    self.error.append(UninitMModel(mmodel_name.range, mmodel_name.text))
                # 5.
                else:
                    call_params = node.get_stmt().get_params().get_items() if node.get_stmt().get_params() is not None else []
                    if len(mmodel[0].parameters) != len(call_params):
                        self.error.append(IncorrectParamNum(node.range, len(mmodel[0].parameters), len(call_params)))
                    else:
                        for index in range(len(mmodel[0].parameters)):
                            expec = mmodel[0].parameters[index][0] if len(mmodel[0].parameters[index]) != 0 else None
                            expec_type = expec.type if expec is not None else None
                            call = node.get_stmt().get_params().get_items()[index] if node.get_stmt().get_params() is not None else []
                            call_name = self.table.get(QName(scope, call))
                            call_type = call_name[0].type if len(call_name) != 0 else None
                            if not expec_type is None and not call_type is None and not expec_type.derives_from(call_type):
                                self.error.append(ParamIncorrectType(call.range, expec_type, call_type))
            if type(node) == SimpleStmt and type(node.get_stmt()) == FunctionCall:
                function_name = node.get_stmt().get_function_name()
                function = self.table.get(QName(BaseScope(), function_name))
                if len(function) == 0:
                    self.error.append(UninitFunction(function_name.range, function_name.text))
                # 5.
                else:
                    call_params = node.get_stmt().get_params().get_items() if node.get_stmt().get_params() is not None else []
                    if len(function[0].parameters) != len(call_params):
                        self.error.append(IncorrectParamNum(node.range, len(function[0].parameters), len(call_params)))
                    else:
                        for index in range(len(function[0].parameters)):
                            expec = function[0].parameters[index][0] if len(function[0].parameters[index]) != 0 else None
                            expec_type = expec.type if expec is not None else None
                            call = node.get_stmt().get_params().get_items()[index] if node.get_stmt().get_params() is not None else []
                            call_name = self.table.get(QName(scope, call))
                            call_type = call_name[0].type if len(call_name) != 0 else None
                            if not expec_type is None and not call_type is None and not expec_type.derives_from(call_type):
                                self.error.append(ParamIncorrectType(call.range, expec_type, call_type))

    def check_parse_tree_function(self, function, scope):
        # check the expression
        params = function.get_params()
        if params == None:
            return
        params = params.get_items()
        expr = function.get_expr()
        used = self.check_expr_undefined(params, expr)
        self.check_param_unused(used, params)

    def check_expr_undefined(self, params, expr):
        used = set()
        #   1.1 referencing undefined parameters
        for child in expr.children:
            if child is None or isinstance(child, Operator) or isinstance(child, Number):
                continue
            if isinstance(child, VarName):
                name = child.get_name()
                used.add(name)
                if name not in params:
                    self.error.append(RefUndefined(name.range, name.text))
            elif child.children != None:
                used = set.union(used, self.check_expr_undefined(params, child))
        return used
    
    def check_param_unused(self, used, params):
        for param in params:
            if param not in used:
                self.warning.append(UnusedParameter(param.range, param.text))
          
    def check_parse_tree_mmodel(self, mmodel, scope):
        lines = set()
        used = set()
        stmt_list = mmodel.get_stmt_list()
        params = mmodel.get_params()
        if params == None:
            params = set()
        else:
            params = set(params.get_items())
        for node in stmt_list.children:
            if node is None:
                continue
            # 2. syntax issue when parsing the grammar
            self.check_syntax_issues(node)
            #   1.1 referencing undefined parameters
            if type(node) == SimpleStmt and type(node.get_stmt()) == Reaction:
                reaction = node.get_stmt()
                rate_law = reaction.get_rate_law()
                used = set.union(used, self.check_rate_law(rate_law, scope, params))
            # 3. 
            if type(node) == SimpleStmt and (type(node.get_stmt()) == Reaction or \
                                               type(node.get_stmt()) == Assignment or \
                                               type(node.get_stmt()) == Declaration or \
                                               type(node.get_stmt()) == ModularModelCall or \
                                               type(node.get_stmt()) == FunctionCall or \
                                               type(node.get_stmt()) == VariableIn):
                if type(node.get_stmt()) == Declaration:
                    for item in node.get_stmt().get_items():
                        maybein = item.get_maybein()
                        if maybein is not None and maybein.is_in_comp():
                            comp = maybein.get_comp()
                            compt = self.table.get(QName(scope, comp.get_name()))
                            if compt[0].value_node is None:
                                # 3. add warning
                                self.warning.append(UninitCompt(comp.get_name().range, comp.get_name_text()))
                elif type(node.get_stmt()) == VariableIn:
                    comp = node.get_stmt().get_incomp().get_comp()
                    compt = self.table.get(QName(scope, comp.get_name()))
                    if compt[0].value_node is None:
                        # 3. add warning
                        self.warning.append(UninitCompt(comp.get_name().range, comp.get_name_text()))
                    # also check if the parameter is defined or not
                    param_name = node.get_stmt().get_name()
                    matched_param = self.table.get(QName(scope, param_name.get_name()))
                    if matched_param[0].value_node is None:
                        self.error.append(RefUndefined(param_name.get_name().range, param_name.get_name_text()))
                else:
                    maybein = node.get_stmt().get_maybein()
                    if maybein is not None and maybein.is_in_comp():
                        comp = maybein.get_comp()
                        compt = self.table.get(QName(scope, comp.get_name()))
                        if compt[0].value_node is None:
                            # 3. add warning
                            self.warning.append(UninitCompt(comp.get_name().range, comp.get_name_text()))
            #   1.1 referencing undefined parameters
            if type(node) == SimpleStmt and type(node.get_stmt()) == Reaction:
                reaction = node.get_stmt()
                rate_law = reaction.get_rate_law()
                self.check_rate_law(rate_law, scope)
                # check if all species have been initialized
                species_list = []
                for species in reaction.get_reactants():
                    species_list.append(species)
                for species in reaction.get_products():
                    species_list.append(species)
                for species in species_list:
                    species_name = species.get_name()
                    matched_species = self.table.get(QName(scope, species_name))
                    if matched_species[0].value_node is None:
                        self.warning.append(SpeciesUndefined(species.range, species_name))
            # 4. 
            if type(node) == SimpleStmt and type(node.get_stmt()) == ModularModelCall:
                mmodel_name = node.get_stmt().get_mmodel_name()
                mmodel = self.table.get(QName(BaseScope(), mmodel_name))
                if len(mmodel) == 0:
                    self.error.append(UninitMModel(mmodel_name.range, mmodel_name.text))
                # 5.
                else:
                    call_params = node.get_stmt().get_params().get_items() if node.get_stmt().get_params() is not None else []
                    if len(mmodel[0].parameters) != len(call_params):
                        self.error.append(IncorrectParamNum(node.range, len(mmodel[0].parameters), len(call_params)))
                    else:
                        for index in range(len(mmodel[0].parameters)):
                            expec = mmodel[0].parameters[index][0] if len(mmodel[0].parameters[index]) != 0 else None
                            expec_type = expec.type if expec is not None else None
                            call = node.get_stmt().get_params().get_items()[index] if node.get_stmt().get_params() is not None else []
                            call_name = self.table.get(QName(scope, call))
                            call_type = call_name[0].type if len(call_name) != 0 else None
                            if not expec_type is None and not call_type is None and not expec_type.derives_from(call_type):
                                self.error.append(ParamIncorrectType(call.range, expec_type, call_type))
            if type(node) == SimpleStmt and type(node.get_stmt()) == FunctionCall:
                function_name = node.get_stmt().get_function_name()
                function = self.table.get(QName(BaseScope(), function_name))
                if len(function) == 0:
                    self.error.append(UninitFunction(function_name.range, function_name.text))
                # 5.
                else:
                    call_params = node.get_stmt().get_params().get_items() if node.get_stmt().get_params() is not None else []
                    if len(function[0].parameters) != len(call_params):
                        self.error.append(IncorrectParamNum(node.range, len(function[0].parameters), len(call_params)))
                    else:
                        for index in range(len(function[0].parameters)):
                            expec = function[0].parameters[index][0] if len(function[0].parameters[index]) != 0 else None
                            expec_type = expec.type if expec is not None else None
                            call = node.get_stmt().get_params().get_items()[index] if node.get_stmt().get_params() is not None else []
                            call_name = self.table.get(QName(scope, call))
                            call_type = call_name[0].type if len(call_name) != 0 else None
                            if not expec_type is None and not call_type is None and not expec_type.derives_from(call_type):
                                self.error.append(ParamIncorrectType(call.range, expec_type, call_type))
        self.check_param_unused(used, params)

    def check_rate_law(self, rate_law, scope, params=set()):
        used = set()
        for leaf in rate_law.scan_leaves():
            if isinstance(leaf, Name):
                text = leaf.text
                used.add(leaf)
                sym = self.table.get(QName(scope, leaf))
                val = sym[0].value_node
                if val is None and sym[0].type != SymbolType.Species and leaf not in params:
                    self.error.append(RefUndefined(leaf.range, text))
                if val is None and sym[0].type == SymbolType.Species:
                    self.warning.append(SpeciesUndefined(leaf.range, text))
        return used

    def get_unique_name(self, prefix: str):
        return self.table.get_unique_name(prefix)

    def handle_child_incomp(self, scope: AbstractScope, node: TrunkNode):
        '''Find all `incomp` nodes among the descendants of node and record the compartment names.'''
        for child in node.descendants():
            # isinstance() is too slow here
            if child and type(child) == InComp:
                child = cast(InComp, child)
                self.table.insert(QName(scope, child.get_comp().get_name()), SymbolType.Compartment)

    def handle_arith_expr(self, scope: AbstractScope, expr: TreeNode):
        # TODO handle dummy tokens
        if not hasattr(expr, 'children'):
            if type(expr) == Name:
                leaf = cast(Name, expr)
                self.table.insert(QName(scope, leaf), SymbolType.Parameter)
        else:
            expr = cast(TrunkNode, expr)
            for leaf in expr.scan_leaves():
                if type(leaf) == Name:
                    leaf = cast(Name, leaf)
                    self.table.insert(QName(scope, leaf), SymbolType.Parameter)

    def handle_reaction(self, scope: AbstractScope, reaction: Reaction):
        name = reaction.get_name()
        if name is not None:
            self.table.insert(QName(scope, name), SymbolType.Reaction, reaction)

        for species in chain(reaction.get_reactants(), reaction.get_products()):
            self.table.insert(QName(scope, species.get_name()), SymbolType.Species)
        self.handle_arith_expr(scope, reaction.get_rate_law())

    def handle_assignment(self, scope: AbstractScope, assignment: Assignment):
        self.table.insert(QName(scope, assignment.get_name()), SymbolType.Parameter,
                            value_node=assignment)
        self.handle_arith_expr(scope, assignment.get_value())

    def resolve_variab(self, tree) -> Variability:
        return {
            'var': Variability.VARIABLE,
            'const': Variability.CONSTANT,
        }[tree.data]

    def resolve_var_type(self, tree) -> SymbolType:
        return {
            'species': SymbolType.Species,
            'compartment': SymbolType.Compartment,
            'formula': SymbolType.Parameter,
        }[tree.data]

    def handle_declaration(self, scope: AbstractScope, declaration: Declaration):
        # TODO add modifiers in table
        modifiers = declaration.get_modifiers()
        # TODO deal with variability
        variab = modifiers.get_variab()
        stype = modifiers.get_type()

        # Skip comma separators
        for item in declaration.get_items():
            name = item.get_maybein().get_var_name().get_name()
            value = item.get_value()

            # TODO update variability
            # If there is value assignment (value is not None), then record the declaration item
            # as the value node. Otherwise put None. See that we can't directly put "value" as
            # argument "valud_node" since they are different things
            value_node = item if value else None
            self.table.insert(QName(scope, name), stype, declaration, value_node)
            if value:
                self.handle_arith_expr(scope, value)
    
    def handle_annotation(self, scope: AbstractScope, annotation: Annotation):
        name = annotation.get_var_name().get_name()
        # TODO(Gary) maybe we can have a narrower type here, since annotation is restricted only to
        # species or compartments? I'm not sure. If that's the case though, we'll need union types.
        qname = QName(scope, name)
        self.table.insert(qname, SymbolType.Parameter)
        self.table.insert_annotation(qname, annotation)
    
    def handle_unit_declaration(self, scope: AbstractScope, unitdec: UnitDeclaration):
        varname = unitdec.get_var_name().get_name()
        unit_sum = unitdec.get_unit_sum()
        qname = QName(scope, varname)
        self.table.insert(qname, SymbolType.Unit)
    
    def handle_unit_assignment(self, scope: AbstractScope, unitdec: UnitDeclaration):
        varname = unitdec.get_var_name().get_name()
        unit_sum = unitdec.get_unit_sum()
        symbols = self.table.get(QName(scope, varname))
        qname = QName(scope, varname)
        self.table.insert(qname, SymbolType.Unit)
        if symbols:
            sym = symbols[0]
            value_node = sym.value_node
            if isinstance(value_node, Assignment):
                value_node.children = (value_node.children[0], value_node.children[1], value_node.children[2], unit_sum)
            elif isinstance(value_node, DeclItem):
                decl_assignment = value_node.children[1]
                decl_assignment.children = (decl_assignment.children[0], decl_assignment.children[1], unit_sum)
    
    def handle_mmodel_call(self, scope: AbstractScope, mmodel_call: ModularModelCall):
        if mmodel_call.get_name() is None:
            name = mmodel_call.get_mmodel_name()
        else:
            name = mmodel_call.get_name()
        self.table.insert(QName(scope, name), SymbolType.Parameter,
                    value_node=mmodel_call)
        
    def handle_function_call(self, scope: AbstractScope, function_call: FunctionCall):
        self.table.insert(QName(scope, function_call.get_name()), SymbolType.Parameter,
                    value_node=function_call)
    
    def handle_variable_in(self, scope: AbstractScope, variable_in: VariableIn):
        name = variable_in.get_name().get_name()
        comp = variable_in.get_incomp().get_comp()
        self.table.insert(QName(scope, name), SymbolType.Variable, decl_node=variable_in)


    def handle_parameters(self, scope: AbstractScope, parameters: Parameters):
        for parameter in parameters.get_items():
            qname = QName(scope, parameter)
            self.table.insert(qname, SymbolType.Parameter)
    
    def handle_function(self, function):
        if function.get_params() is not None:
            params = function.get_params().get_items()
        else:
            params = []
        scope = ModularModelScope(str(function.get_name()))
        parameters = []
        for name in params:
            # get symbols
            qname = self.resolve_qname(QName(scope, name))
            parameters.append(qname)
        self.table.insert_function(QName(BaseScope(), function), SymbolType.Function, parameters)
        self.table.insert_function(QName(FunctionScope(str(function.get_name())), function), SymbolType.Function, parameters)

    def handle_mmodel(self, mmodel):
        logging.debug("AAAAA")
        # find all type information
        if mmodel.get_params() is not None:
            params = mmodel.get_params().get_items()
        else:
            params = []
        scope = ModularModelScope(str(mmodel.get_name()))
        parameters = []
        for name in params:
            # get symbols
            qname = self.resolve_qname(QName(scope, name))
            parameters.append(qname)
        self.table.insert_mmodel(QName(BaseScope(), mmodel), SymbolType.ModularModel, parameters)
        self.table.insert_mmodel(QName(ModularModelScope(str(mmodel.get_name())), mmodel), SymbolType.ModularModel, parameters)

    def check_syntax_issues(self, node):
        if type(node) == ErrorToken:
            node = cast(ErrorToken, node)
            if node.text.strip() == '':
                # this must be an unexpected newline
                self.error.append(UnexpectedNewlineIssue(node.range.start))
            else:
                self.error.append(UnexpectedTokenIssue(node.range, node.text))
        # 2. syntax issue when parsing the grammar
        elif type(node) == ErrorNode:
            node = cast(ErrorNode, node)
            last_leaf = node.last_leaf()
            if last_leaf and last_leaf.next is None:
                self.error.append(UnexpectedEOFIssue(last_leaf.range))

# def get_ancestors(node: ASTNode):
#     ancestors = list()
#     while True:
#         parent = getattr(node, 'parent')
#         if parent is None:
#             break
#         ancestors.append(parent)
#         node = parent

#     return ancestors


# def find_node(nodes: List[Tree], data: str):
#     for node in nodes:
#         if node.data == data:
#             return node
#     return None
