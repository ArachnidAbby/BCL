class VariableAssign(ASTNode):
    '''Handles Variable Assignment and Variable Instantiation.'''
    __slots__ = ('value', 'block', 'is_declaration', 'var_name', 'explicit_typ', 'typ')
    # type = NodeTypes.EXPRESSION
    # name = "varAssign"

    def __init__(self, pos: SrcPosition, name: str, value, block, typ = Void()):
        self._position = pos
        self.var_name = name
        self.is_declaration = False
        self.value = value
        self.block = block
        self.explicit_typ = typ!=Void # TODO: GROSS AS FUCK
        self.typ = typ

    def pre_eval(self, func):
        self.value.pre_eval(func)

        if self.block!=None and self.var_name not in self.block.variables.keys():
            self.typ = self.typ.as_type_reference()
            self.block.variables[self.var_name] = VariableObj(None, self.typ, False)
            self.is_declaration = True
        if not self.is_declaration and self.explicit_typ:
            error("Cannot declare the type of a variable after initial declaration", line = self.position)

        if self.block.get_variable(self.var_name).type.is_void():
            self.block.variables[self.var_name].type = self.value.ret_type
        
        if (self.block.get_variable(self.var_name), self.var_name) not in func.variables:
            variable = self.block.get_variable(self.var_name)
            func.variables.append((variable, self.var_name))
    
    def eval(self, func):
        self.value.pre_eval(func)
        variable = self.block.get_variable(self.var_name)
        if self.block.validate_variable(self.var_name):
            self.block.variables[self.var_name].is_constant = False

        variable.store(func, self.value)

class VariableIndexPutAt(ASTNode): # TODO: CONSOLIDATE FUNCTIONALITY INTO ABOVE CLASS
    __slots__ = ('value', 'ref')
    name = "varIndPutAt"

    def __init__(self, pos: SrcPosition, varindref: VariableIndexRef, value: ExpressionNode):
        self._position = pos
        self.ref = varindref
        self.value = value
    
    def pre_eval(self, func):
        self.ref.pre_eval(func)
        self.value.pre_eval(func)
    
    def eval(self, func):
        return self.ref.varref.ret_type.put(func, self.ref, self.value)

    def __repr__(self) -> str:
        return f"<putat for `{self.ref}`>"