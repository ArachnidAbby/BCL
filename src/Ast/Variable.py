from llvmlite import ir
from .Nodes import AST_NODE

class VariableAssign(AST_NODE):
    def init(self, name, value):
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
    def init(self, name):
        self.name = name
        self.type = "variableRef"
    
    def eval(self, func):
        ptr = func.block.variables[self.name]
        return func.builder.load(ptr)