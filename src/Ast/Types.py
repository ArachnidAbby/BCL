from typing import List
from llvmlite import ir

from .Nodes import AST_NODE

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
    def convert_from(typ: str, previous):
        if typ!= 'i32': previous.fptosi(Integer_32.ir_type)
        
        return previous

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)

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
    def convert_from(typ: str, previous):
        if typ!= 'f64': previous.sitofp(Float_64.ir_type)
        
        return previous


    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)

types = {
    "i32": Integer_32,
    'f64': Float_64
}

def list_type_conversion(objs: List[AST_NODE]):
    '''When a math operation happens between types, we need to know what the final return type will be.'''
    conversion_priority_raw = ['i32', 'i64', 'f64', 'f128'] # the further down the list this is, the higher priority
    conversion_priority = {x: c for c,x in enumerate(conversion_priority_raw)}

    largest_priority = max(
        [conversion_priority[x.ret_type] for x in objs]
    )

    return conversion_priority_raw[largest_priority]

def type_conversion(self: AST_NODE,  other: AST_NODE):
    '''When a math operation happens between types, we need to know what the final return type will be.'''
    conversion_priority_raw = ['i32', 'i64', 'f64', 'f128'] # the further down the list this is, the higher priority
    conversion_priority = {x: c for c,x in enumerate(conversion_priority_raw)}

    largest_priority = max(
        conversion_priority[self.ret_type],
        conversion_priority[other.ret_type]
    )

    return conversion_priority_raw[largest_priority]