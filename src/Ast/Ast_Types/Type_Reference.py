from Ast import Ast_Types
from Ast.nodetypes import NodeTypes
from errors import error
from llvmlite import ir

from . import Type_Base


class Reference(Type_Base.Type):
    __slots__ = tuple("typ")
    
    name = 'ref'
    pass_as_ptr = False

    def __init__(self, typ: Type_Base.Type):
        self.typ = typ
        self.ir_type = typ.ir_type.as_pointer()
    
    def convert_to(self, func, orig, typ):
        error(f"Pointer conversions are not supported due to unsafe behavior", line = orig.position)

    def get_op_return(self, op: str, lhs, rhs):
        self.typ.get_op_return(op, lhs, rhs)
    
    def sum(self, func, lhs, rhs): 
        return lhs.typ.sum(func, lhs.as_varref(), rhs)

    
    def sub(self, func, lhs, rhs): 
        return lhs.typ.sub(func, lhs.as_varref(), rhs)

    
    def mul(self, func, lhs, rhs): 
        return lhs.typ.mul(func, lhs.as_varref(), rhs)

    
    def div(self, func, lhs, rhs): 
        return lhs.typ.div(func, lhs.as_varref(), rhs)

    
    def mod(self, func, lhs, rhs): 
        return lhs.typ.mod(func, lhs.as_varref(), rhs)

    
    
    def eq(self, func, lhs, rhs): 
        return lhs.typ.eq(func, lhs.as_varref(), rhs)
    
    def neq(self, func, lhs, rhs):
        return lhs.typ.neq(func, lhs.as_varref(), rhs)
    
    def geq(self, func, lhs, rhs):
        return lhs.typ.geq(func, lhs.as_varref(), rhs)
    
    def leq(self, func, lhs, rhs):
        return lhs.typ.leq(func, lhs.as_varref(), rhs)
    
    def le(self, func, lhs, rhs):
        return lhs.typ.le(func, lhs.as_varref(), rhs)
    
    def gr(self, func, lhs, rhs):
        return lhs.typ.gr(func, lhs.as_varref(), rhs)
