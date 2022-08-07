from llvmlite import ir

from Ast import Types

from .Nodes import AST_NODE


class VariableAssign(AST_NODE):
    '''Handles Variable Assignment and Variable Instantiation.'''
    __slots__ = ["value"]

    def init(self, name: str, value, block):
        self.name = name
        self.type = "variableAssign"
        self.value = value

        if block!=None:
            block.variables[self.name] = (None, self.value.ret_type, False)
        else:
            raise Exception("No Block for Variable Assignment to take place in")
        
    def pre_eval(self):
        self.value.pre_eval()
    
    def eval(self, func):
        self.value.pre_eval()
                
        if func.block.variables[self.name][0]==None:
            ptr = func.builder.alloca(self.value.ir_type, name=self.name)
            func.block.variables[self.name] = (ptr, self.value.ret_type, False)
        else:
            ptr = func.block.variables[self.name][0]
            func.block.variables[self.name][2] = False

        func.builder.store(self.value.eval(func), ptr)

class VariableRef(AST_NODE):
    '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`'''
    __slots__ = ['block', 'ir_type']

    def init(self, name: str, block):
        self.name = name
        self.type = "variableRef"
        self.block = block
    
    def pre_eval(self):
        self.ret_type = self.block.variables[self.name][1] # get variable type {name: (ptr, type, is_const)}
        self.ir_type = Types.types[self.ret_type]
    
    def eval(self, func):
        ptr = func.block.variables[self.name][0] # get variable ptr
        # print(func.block.variables[self.name])
        if not func.block.variables[self.name][2]: return func.builder.load(ptr) # var[2] is whether or not this is a static var
        else: return ptr
