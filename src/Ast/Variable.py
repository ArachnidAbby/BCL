from llvmlite import ir

from .Nodes import AST_NODE


class VariableAssign(AST_NODE):
    '''Handles Variable Assignment and Variable Instantiation.'''
    __slots__ = ["value"]

    def init(self, name: str, value, block):
        self.name = name
        self.type = "variableAssign"
        self.value = value

        if block!=None:
            block.variables[self.name] = (None, self.value.ret_type)
        else:
            raise Exception("No Block for Variable Assignment to take place in")
    
    def eval(self, func):
        if func.block.variables[self.name][0]==None:
            ptr = func.builder.alloca(self.value.ir_type, name=self.name)
            func.block.variables[self.name] = (ptr, self.value.ret_type)
        else:
            ptr = func.block.variables[self.name][0]

        func.builder.store(self.value.eval(func), ptr)

class VariableRef(AST_NODE):
    '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`'''
    __slots__ = []

    def init(self, name: str, block):
        self.name = name
        self.type = "variableRef"
        print(block)
        self.ret_type = block.variables[self.name][1] # get variable type {name: (ptr, type)}
    
    def eval(self, func):
        ptr = func.block.variables[self.name][0] # get variable ptr
        return func.builder.load(ptr)
