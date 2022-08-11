from Errors import error
from llvmlite import ir

from Ast import Types

from .Nodes import AST_NODE


class VariableObj:
    '''allows variables to be stored on the heap. This lets me pass them around by reference.'''
    __slots__ = ["ptr", "type", "is_constant"]

    def __init__(self, ptr, typ, is_constant):
        self.ptr = ptr
        self.type = typ
        self.is_constant = is_constant

class VariableAssign(AST_NODE):
    '''Handles Variable Assignment and Variable Instantiation.'''
    __slots__ = ["value", 'block']

    def init(self, name: str, value, block):
        self.name = name
        self.type = "variableAssign"
        self.value = value
        self.block = block

        if block!=None:
            block.variables[self.name] = VariableObj(None, self.value.ret_type, False)
        else:
            raise Exception("No Block for Variable Assignment to take place in")
        
    def pre_eval(self):
        self.value.pre_eval()
        self.block.variables[self.name].type = self.value.ret_type
    
    def eval(self, func):
        self.value.pre_eval()
        variable = func.block.get_variable(self.name)

        if not self.block.validate_variable(self.name):
            ptr = func.builder.alloca(self.value.ir_type, name=self.name)
            variable.ptr = ptr
        else:
            ptr = variable.ptr
            if self.value.ret_type != variable.type:
                error(
                    f"Cannot store type '{self.value.ret_type}' in variable '{self.name}' of type {func.block.variables[self.name].type}",
                    line = self.position
                )
            func.block.variables[self.name].is_constant = False

        func.builder.store(self.value.eval(func), ptr)

class VariableRef(AST_NODE):
    '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`'''
    __slots__ = ['block', 'ir_type']

    def init(self, name: str, block):
        self.name = name
        self.type = "variableRef"
        self.block = block
    
    def pre_eval(self):
        self.ret_type = self.block.get_variable(self.name).type
        self.ir_type = Types.types[self.ret_type].ir_type
    
    def eval(self, func):
        ptr = func.block.get_variable(self.name).ptr 
        if not func.block.get_variable(self.name).is_constant: return func.builder.load(ptr) 
        else: return ptr
