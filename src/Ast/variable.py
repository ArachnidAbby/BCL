from errors import error

from Ast.nodetypes import NodeTypes

from .Ast_Types import Type_Base, Void
from .nodes import ASTNode, ExpressionNode


class VariableObj:
    '''allows variables to be stored on the heap. This lets me pass them around by reference.'''
    __slots__ = ("ptr", "type", "is_constant")

    def __init__(self, ptr, typ, is_constant):
        self.ptr = ptr
        self.type = typ
        if isinstance(typ, str):
            self.type = Type_Base.types_dict[typ]()
        self.is_constant = is_constant
    
    def define(self, func):
        '''alloca memory for the variable'''
        ptr = func.builder.alloca(self.type.ir_type)
        self.ptr = ptr
        return ptr
    
    def store(self, func, value):
        func.builder.store(value.eval(func), self.ptr)

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
    
    def eval(self, func):
        self.value.pre_eval()
        variable = self.block.get_variable(self.name)

        if not self.block.validate_variable(self.name):
            variable.define(func)
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
        self.ret_type = self.block.get_variable(self.name).type
        if self.block.get_variable(self.name).type.name=="UNKNOWN":
            error(f"Unknown variable '{self.name}'", line = self.position)

        self.ir_type = self.ret_type.ir_type
    
    def eval(self, func):
        ptr = self.block.get_variable(self.name).ptr 
        if not self.block.get_variable(self.name).is_constant: return func.builder.load(ptr) 
        else: return ptr

    def __repr__(self) -> str:
        return f"<VariableRef to `{self.name}`>"
