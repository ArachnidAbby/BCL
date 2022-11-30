from errors import error, inline_warning
from llvmlite import ir

from Ast import Ast_Types, Literal, exception
from Ast.nodetypes import NodeTypes

from .Ast_Types import Type_Base, Void
from .nodes import ASTNode, ExpressionNode

ZERO_CONST = const = ir.Constant(ir.IntType(64), 0)

class VariableObj:
    '''allows variables to be stored on the heap. This lets me pass them around by reference.'''
    __slots__ = ("ptr", "type", "is_constant", "prev_load", "changed")

    def __init__(self, ptr, typ, is_constant):
        self.ptr = ptr
        self.type = typ
        if isinstance(typ, str):
            self.type = Type_Base.types_dict[typ]()
        self.is_constant = is_constant
        self.changed = False
        self.prev_load = None # prevents multiple loads from memory when zero changes have happened
    
    def define(self, func, name):
        '''alloca memory for the variable'''
        ptr = func.builder.alloca(self.type.ir_type, name=name)
        self.ptr = ptr
        return ptr
    
    def store(self, func, value):
        self.changed = True
        func.builder.store(value.eval(func), self.ptr)
    
    def get_value(self, func):
        if not self.changed and self.prev_load is not None:
            return self.prev_load

        self.changed = False
        if not self.is_constant: 
            self.prev_load = func.builder.load(self.ptr) 
            return self.prev_load
        return self.ptr
        

    def __repr__(self) -> str:
        return f'VAR: |{self.ptr}, {self.type}|'

class VariableAssign(ASTNode):
    '''Handles Variable Assignment and Variable Instantiation.'''
    __slots__ = ("value", 'block', 'is_declaration')
    type = NodeTypes.EXPRESSION

    def init(self, name: str, value, block):
        self.name = name
        self.is_declaration = False
        self.value = value
        self.block = block

        if block!=None and self.name not in block.variables.keys():
            block.variables[self.name] = VariableObj(None, Void(), False)
            self.is_declaration = True

        elif block==None:
            raise Exception("No Block for Variable Assignment to take place in")
        
    def pre_eval(self):
        self.value.pre_eval()
        self.block.variables[self.name].type = self.value.ret_type
        self.block.variables[self.name].changed = True
    
    def eval(self, func):
        self.value.pre_eval()
        variable = self.block.get_variable(self.name)

        if not self.block.validate_variable(self.name):
            variable.define(func, self.name)
        else:
            if self.value.ret_type != variable.type:
                error(
                    f"Cannot store type '{self.value.ret_type}' in variable '{self.name}' of type {self.block.variables[self.name].type}",
                    line = self.position
                )
            self.block.variables[self.name].is_constant = False

        variable.store(func, self.value)

class VariableRef(ExpressionNode):
    '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`'''
    __slots__ = ('block')

    def init(self, name: str, block):
        self.name = name
        self.block = block
    
    def pre_eval(self):
        if not self.block.validate_variable_exists(self.name):
            error(f"Undefined variable '{self.name}'", line = self.position)

        self.ret_type = self.block.get_variable(self.name).type
        if self.block.get_variable(self.name).type.name=="UNKNOWN":
            error(f"Unknown variable '{self.name}'", line = self.position)

        self.ir_type = self.ret_type.ir_type
    
    def eval(self, func):
        return self.block.get_variable(self.name).get_value(func)

    def get_ptr(self, func):
        return self.block.get_variable(self.name).ptr 

    def __repr__(self) -> str:
        return f"<VariableRef to `{self.name}`>"

class VariableIndexRef(ExpressionNode):
    '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`'''
    __slots__ = ('ind', 'varref')
    name = "varIndRef"

    def init(self, varref: VariableRef, ind: ExpressionNode):
        self.varref = varref
        self.ind = ind
    
    def pre_eval(self):
        self.varref.pre_eval()
        self.ind.pre_eval()
        self.ret_type = self.varref.ret_type.typ
        self.ir_type = self.ret_type.ir_type

    def check_valid_literal(self, lhs, rhs):
        if rhs.name == "literal" and lhs.ir_type.count-1 < rhs.value:
            error(f'Array index out range. Max size \'{lhs.ir_type.count}\'', line = rhs.position)
        
        if rhs.ret_type.name not in ("i32", "i64", "i16", "i8"):
            error(f'Array index operation must use an integer index. type used: \'{rhs.ret_type}\'', line = rhs.position)
    
    def get_ptr(self, func) -> ir.Instruction:
        self.check_valid_literal(self.varref, self.ind)
        if self.ind.name != "literal": #* error checking at runtime
            size = Literal((-1,-1,-1), self.varref.ir_type.count-1, Ast_Types.Integer_32())
            cond = self.ind.ret_type.leq(func, size, self.ind)
            with func.builder.if_then(cond) as if_block:
                exception.over_index_exception(func, self.varref.name, self.ind.eval(func), self.position)
        return func.builder.gep(self.varref.get_ptr(func) , [ZERO_CONST, self.ind.eval(func),])

    def eval(self, func):
        return self.varref.ret_type.index(func, self)

    def __repr__(self) -> str:
        return f"<VariableRef to `{self.name}`>"

class VariableIndexPutAt(ASTNode):
    __slots__ = ('value', 'ref')
    name = "varIndPutAt"

    def init(self, varindref: VariableRef, value: ExpressionNode):
        self.ref = varindref
        self.value = value
    
    def pre_eval(self):
        self.ref.pre_eval()
        self.value.pre_eval()
    
    def eval(self, func):
        return self.ref.varref.ret_type.put(func, self.ref, self.value)

    def __repr__(self) -> str:
        return f"<VariableRef to `{self.name}`>"
