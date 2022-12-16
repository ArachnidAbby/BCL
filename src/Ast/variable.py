from errors import error, inline_warning
from llvmlite import ir

from Ast import Ast_Types, Literal, exception
from Ast.nodetypes import NodeTypes
from Ast.varobject import VariableObj

from .Ast_Types import Void
from .nodes import ASTNode, ExpressionNode

ZERO_CONST = ir.Constant(ir.IntType(64), 0)

class VariableAssign(ASTNode):
    '''Handles Variable Assignment and Variable Instantiation.'''
    __slots__ = ('value', 'block', 'is_declaration', 'var_name', 'explicit_typ', 'typ')
    type = NodeTypes.EXPRESSION
    name = "varAssign"

    def init(self, name: str, value, block, typ = Void()):
        self.var_name = name
        self.is_declaration = False
        self.value = value
        self.block = block
        self.explicit_typ = typ!=Void
        self.typ = typ
        
        
    def pre_eval(self, func):
        self.value.pre_eval(func)

        if self.block!=None and self.var_name not in self.block.variables.keys():
            if self.typ.name == "literal":
                self.typ.eval(None)
                typ = self.typ.value
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

class VariableRef(ExpressionNode):
    '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`'''
    __slots__ = ('block', 'var_name')
    name = "varRef"

    def init(self, name: str, block):
        self.var_name = name
        self.block = block
    
    def pre_eval(self, func):
        if not self.block.validate_variable_exists(self.var_name):
            error(f"Undefined variable '{self.var_name}'", line = self.position)

        self.ret_type = self.block.get_variable(self.var_name).type
        if self.block.get_variable(self.var_name).type.is_void():
            error(f"undefined variable '{self.var_name}'", line = self.position)

        self.ir_type = self.ret_type.ir_type
    
    def eval(self, func):
        return self.block.get_variable(self.var_name).get_value(func)

    def get_ptr(self, func):
        return self.block.get_variable(self.var_name).ptr 
    
    def get_var(self, func):
        return self.block.get_variable(self.var_name)
    
    def get_value(self, func):
        '''only important in references'''
        self.ret_type = self.ret_type.typ
        return self

    def __repr__(self) -> str:
        return f"<VariableRef to '{self.var_name}'>"

    def __str__(self) -> str:
        return self.var_name

class Ref(ExpressionNode):
    '''Variable Reference that acts like other `expr` nodes. It returns a ptr uppon `eval`'''
    __slots__ = ('var', )
    name = "ref"

    def init(self, var):
        self.var = var
        
    
    def pre_eval(self, func):
        self.var.pre_eval(func)
        self.ret_type = Ast_Types.Reference(self.var.ret_type)

        self.ir_type = self.ret_type.ir_type
    
    def eval(self, func):
        return self.var.get_ptr(func)
    
    def get_var(self, func):
        return self.var.get_var(func)

    def get_value(self, func):
        return self.var

    def get_ptr(self, func):
        return self.var.get_ptr(func)

    def __repr__(self) -> str:
        return f"<Ref to '{self.var}'>"

    def __str__(self) -> str:
        return self.var

class VariableIndexRef(ExpressionNode):
    '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`'''
    __slots__ = ('ind', 'varref', 'var_name', 'size')
    name = "varIndRef"

    def init(self, varref: VariableRef, ind: ExpressionNode):
        self.varref = varref
        self.ind = ind
        self.size = 0
    
    def pre_eval(self, func):
        self.varref.pre_eval(func)
        if self.varref.ret_type.name == "ref":
            self.varref = self.varref.get_value(func)
            self.varref.ir_type = self.varref.ret_type.ir_type
        
        self.ind.pre_eval(func)
        if self.ind.ret_type.name == "ref":
            self.ind = self.ind.get_value(func)
        if self.varref.ret_type.get_op_return('ind', None, None) is not None:
            self.ret_type = self.varref.ret_type.typ
        else:
            self.ret_type = self.varref.ret_type
        self.ir_type = self.ret_type.ir_type

    def check_valid_literal(self, lhs, rhs):
        if rhs.name == "literal" and (lhs.ret_type.size-1 < rhs.value or rhs.value < 0): # check inbounds
            error(f'Array index out range. Max size \'{lhs.ret_type.size}\'', line = rhs.position)
        
        if rhs.ret_type.name not in ("i32", "i64", "i16", "i8"):
            error(f'Array index operation must use an integer index. type used: \'{rhs.ret_type}\'', line = rhs.position)
    
    def _out_of_bounds(self, func):
        '''creates the code for runtime bounds checking'''
        size = Literal((-1,-1,-1), self.varref.ir_type.count-1, Ast_Types.Integer_32())
        zero = Literal((-1,-1,-1), 0, Ast_Types.Integer_32())
        cond = self.ind.ret_type.le(func, size, self.ind)
        cond2 = self.ind.ret_type.gr(func, zero, self.ind)
        condcomb = func.builder.or_(cond, cond2)
        with func.builder.if_then(condcomb) as if_block:
            exception.over_index_exception(func, self.varref, self.ind.eval(func), self.position)
    
    def get_ptr(self, func) -> ir.Instruction:
        self.check_valid_literal(self.varref, self.ind)
        if self.ind.name != "literal":#* error checking at runtime
            if self.ind.get_var(func).range is not None:
                rang = self.ind.get_var(func).rang
                arrayrang = range(0, self.varref.ir_type.count)
                if self.ind.name == "varRef" and rang[0] in arrayrang and rang[1] in arrayrang: 
                    return func.builder.gep(self.varref.get_ptr(func) , [ZERO_CONST, self.ind.eval(func),])

            self._out_of_bounds(func)
            
        return func.builder.gep(self.varref.get_ptr(func) , [ZERO_CONST, self.ind.eval(func),])

    def get_value(self, func):
        return self.get_ptr(func)

    def eval(self, func):
        return self.varref.ret_type.index(func, self)

    def __repr__(self) -> str:
        return f"<index of `{self.varref}`>"

class VariableIndexPutAt(ASTNode):
    __slots__ = ('value', 'ref')
    name = "varIndPutAt"

    def init(self, varindref: VariableIndexRef, value: ExpressionNode):
        self.ref = varindref
        self.value = value
    
    def pre_eval(self, func):
        self.ref.pre_eval(func)
        self.value.pre_eval(func)
    
    def eval(self, func):
        return self.ref.varref.ret_type.put(func, self.ref, self.value)

    def __repr__(self) -> str:
        return f"<putat for `{self.ref}`>"
