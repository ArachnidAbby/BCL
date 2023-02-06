from typing import Self

from llvmlite import ir

from Ast import Ast_Types
from Ast.function import _Function
from Ast.nodes import KeyValuePair
from errors import error


class Function(Ast_Types.Type):
    '''abstract type class that outlines the necessary features of a type class.'''

    __slots__ = ('func_name', 'module', 'versions')
    name = "STRUCT"
    pass_as_ptr = False
    no_load = False
    read_only = True

    # TODO: implement struct methods
    def __init__(self, name: str, module):
        self.func_name = name
        self.module = module
        self.versions: dict[tuple, _Function] = {}
        module.globals[name] = self
    
    def create(self, args: tuple, func_ir):
        '''create a function with that name'''
        self.version[args] = func_ir
        

    # TODO: allow casting overloads
    @classmethod
    def convert_from(cls, func, typ, previous) -> ir.Instruction:
        error(f"Function type has no conversions",  line = previous.position)
    
    def convert_to(self, func, orig, typ) -> ir.Instruction:
        error(f"Function type has no conversions",  line = orig.position)

    def __eq__(self, other):
        return super().__eq__(other) and other.struct_name==self.struct_name
    def __neq__(self, other):
        return super().__neq__(other) and other.struct_name!=self.struct_name
    
    # TODO: implement this
    def get_op_return(self, op, lhs, rhs):
        if op == "call": #! Temporary !
            pass

    def get_member(self):
        pass

    # def sum  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '+' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    # def sub  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '-' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    # def mul  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '*' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    # def div  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '/' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    # def mod  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '%' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def pow (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '**' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    
    # def eq   (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '==' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    # def neq  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '!=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def geq  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '>=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    # def leq  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    # def le   (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    # def gr   (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    
    # def _not (self, func, rhs) -> ir.Instruction: error(f"Operator 'not' is not supported for type '{rhs.ret_type}'", line = rhs.position)
    
    # def _and (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator 'and' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    # def _or  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator 'or' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    
    def index(self, func, lhs) -> ir.Instruction:
        return func.builder.load(lhs.get_ptr(func))

    def put(self, func, lhs, value): error(f"Operation 'putat' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def assign(self, func, ptr, value, typ: Self):
    #     val = value.ret_type.convert_to(func, value, typ)  # type: ignore
    #     func.builder.store(val, ptr.ptr)

    # def isum(self, func, ptr, rhs):
    #     final_value = self.sum(func, ptr, rhs)
    #     ptr = ptr.get_ptr(func)
    #     func.builder.store(final_value, ptr)
    
    # def isub(self, func, ptr, rhs):
    #     final_value = self.sub(func, ptr, rhs)
    #     ptr = ptr.get_ptr(func)
    #     func.builder.store(final_value, ptr)
    
    # def imul(self, func, ptr, rhs):
    #     final_value = self.mul(func, ptr, rhs)
    #     ptr = ptr.get_ptr(func)
    #     func.builder.store(final_value, ptr)

    
    # def idiv(self, func, ptr, rhs):
    #     final_value = self.div(func, ptr, rhs)
    #     ptr = ptr.get_ptr(func)
    #     func.builder.store(final_value, ptr)

    
    def __hash__(self):
        return hash(self.name+self.struct_name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}--{self.struct_name}>'
    
    def __str__(self) -> str:
        return self.struct_name

    def __call__(self) -> Self:
        return self
