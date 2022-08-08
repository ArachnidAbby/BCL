from typing import List
from llvmlite import ir
from Errors import error

from .Nodes import AST_NODE


class Integer_1(AST_NODE):
    '''The standard boolean (I1) type implementation that also acts as all other `expr` nodes do.'''
    __slots__ = ["value"]

    ir_type = ir.IntType(1)

    def init(self, value):
        self.value = value
        self.name = "I1"
        self.type = "Literal"
        self.ret_type = "bool"

    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ in ('i32', 'i64'): return func.builder.trunc(previous,Integer_1.ir_type)
        elif typ == 'bool': return previous
        else: error(f"type '{typ}' cannot be converted to type 'bool'", line = previous.position)

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)
    
    def __repr__(self):
        return f"<AST_I1_Literal: {self.value}>"
class Integer_32(AST_NODE):
    '''The standard Integer_32 type implementation that also acts as all other `expr` nodes do.'''
    __slots__ = ["value"]

    ir_type = ir.IntType(32)

    def init(self, value):
        self.value = value
        self.name = "I32"
        self.type = "Literal"
        self.ret_type = "i32"

    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ in ('f64','f128'): return func.builder.fptosi(previous,Integer_32.ir_type)
        elif typ== 'bool': return func.builder.zext(previous, Integer_32.ir_type)
        elif typ == 'i64': return func.builder.trunc(previous, Integer_32.ir_type)
        elif typ == 'i32': return previous

        else: error(f"type '{typ}' cannot be converted to type 'float'",line = previous.position)

    @staticmethod
    def sum(func, lhs, rhs):
        return func.builder.add(lhs, rhs)
    
    @staticmethod
    def sub(func, lhs, rhs):
        return func.builder.sub(lhs, rhs)
    
    @staticmethod
    def mul(func, lhs, rhs):
        return func.builder.mul(lhs, rhs)
    
    @staticmethod
    def div(func, lhs, rhs):
        return func.builder.sdiv(lhs, rhs)
    
    @staticmethod
    def mod(func, lhs, rhs):
        return func.builder.srem(lhs, rhs)
    
    @staticmethod
    def eq(func, lhs, rhs):
        return func.builder.icmp_signed('==', lhs, rhs)
    
    @staticmethod
    def neq(func, lhs, rhs):
        return func.builder.icmp_signed('!=', lhs, rhs)
    
    @staticmethod
    def gr(func, lhs, rhs):
        return func.builder.icmp_signed('>', lhs, rhs)
    
    @staticmethod
    def geq(func, lhs, rhs):
        return func.builder.icmp_signed('>=', lhs, rhs)
    
    @staticmethod
    def le(func, lhs, rhs):
        return func.builder.icmp_signed('<', lhs, rhs)
    
    @staticmethod
    def leq(func, lhs, rhs):
        return func.builder.icmp_signed('<=', lhs, rhs)
    


    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)
    
    def __repr__(self):
        return f"<AST_I32_Literal: {self.value}>"

class Float_64(AST_NODE):
    '''The standard Float_64 type implementation that also acts as all other `expr` nodes do.'''
    __slots__ = ["value"]

    ir_type = ir.FloatType()

    def init(self, value):
        self.value = value
        self.name = "F64"
        self.type = "Literal"
        self.ret_type = "f64"
        
    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ in ('i32', 'i64'): return func.builder.sitofp(previous,Float_64.ir_type)
        elif typ== 'bool': return func.builder.uitofp(previous, Float_64.ir_type)
        elif typ == 'f128': return func.builder.fptrunc(previous, Float_64.ir_type)
        elif typ == 'f64': return previous

        else: error(f"type '{typ}' cannot be converted to type 'float'",line = previous.position)
    
    @staticmethod
    def sum(func, lhs, rhs):
        return func.builder.fadd(lhs, rhs)
    
    @staticmethod
    def sub(func, lhs, rhs):
        return func.builder.fsub(lhs, rhs)
    
    @staticmethod
    def mul(func, lhs, rhs):
        return func.builder.fmul(lhs, rhs)
    
    @staticmethod
    def div(func, lhs, rhs):
        return func.builder.fdiv(lhs, rhs)
    
    @staticmethod
    def mod(func, lhs, rhs):
        return func.builder.frem(lhs, rhs)
    
    @staticmethod
    def eq(func, lhs, rhs):
        return func.builder.fcmp_signed('==', lhs, rhs)

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)

class Void(AST_NODE):
    '''The standard Void type'''
    __slots__ = ["value"]

    ir_type = ir.VoidType()

    def init(self, value):
        self.value = value
        self.name = "Void"
        self.type = "Literal"
        self.ret_type = "void"
        
    @staticmethod
    def convert_from(func, typ: str, previous):
        error(f"'void' cannot be converted to type '{typ}'", line = previous.position)


    def eval(self, func):
        pass

types = {
    'void': Void,
    'bool': Integer_1,
    "i32": Integer_32,
    "int": Integer_32,
    'f64': Float_64,
    'float': Float_64
}

def list_type_conversion(objs: List[AST_NODE]):
    '''When a math operation happens between types, we need to know what the final return type will be.'''
    conversion_priority_raw = ['unkown','bool','i32', 'i64', 'f64', 'f128'] # the further down the list this is, the higher priority
    conversion_priority = {x: c for c,x in enumerate(conversion_priority_raw)}

    largest_priority = max(
        [conversion_priority[x.ret_type] for x in objs]
    )

    return conversion_priority_raw[largest_priority]

def type_conversion(self: AST_NODE,  other: AST_NODE):
    '''When a math operation happens between types, we need to know what the final return type will be.'''
    conversion_priority_raw = ['unknown','bool','i32', 'i64', 'f64', 'f128'] # the further down the list this is, the higher priority
    conversion_priority = {x: c for c,x in enumerate(conversion_priority_raw)}

    largest_priority = max(
        conversion_priority[self.ret_type],
        conversion_priority[other.ret_type]
    )

    return conversion_priority_raw[largest_priority]