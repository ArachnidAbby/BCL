from llvmlite import ir

from .Nodes import AST_NODE


class VariableAssign(AST_NODE):
    '''Handles Variable Assignment and Variable Instantiation.'''
    __slots__ = ["value"]

    def init(self, name: str, value):
        self.name = name
        self.type = "variableAssign"

        self.value = value
    
    def eval(self, func):
        if func.block.variables[self.name]==None:
            ptr = func.builder.alloca(self.value.ir_type, name=self.name)
            func.block.variables[self.name] = ptr
        else:
            ptr = func.block.variables[self.name]

        func.builder.store(self.value.eval(func), ptr)

class VariableRef(AST_NODE):
    '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`'''
    __slots__ = []

    def init(self, name: str):
        self.name = name
        self.type = "variableRef"
    
    def eval(self, func):
        ptr = func.block.variables[self.name]
        return func.builder.load(ptr)
