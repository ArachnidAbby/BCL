from typing import List
from llvmlite import ir

from .Nodes import AST_NODE


class Integer_1(AST_NODE):
    '''The standard Integer_32 type implementation that also acts as all other `expr` nodes do.'''
    __slots__ = ["value"]

    ir_type = ir.IntType(1)

    def init(self, value):
        self.value = value
        self.name = "I1"
        self.type = "Literal"
        self.ret_type = "bool"

    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ!= 'bool': return func.builder.zext(previous, Integer_32.ir_type)
        
        return previous

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
        if typ== 'f64': return func.builder.fptosi(previous,Integer_32.ir_type)
        elif typ== 'bool': return func.builder.zext(previous, Integer_32.ir_type)
        else: return previous


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
    
    # def pre_eval(self)
    
    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ!= 'f64': previous.sitofp(Float_64.ir_type)
        
        return previous


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
    
    # def pre_eval(self)
    
    @staticmethod
    def convert_from(func, typ: str, previous):
        pass


    def eval(self, func):
        pass

# class String_Literal(AST_NODE):
#     __slots__ = ["value", "ir_type"]

#     def init(self, value, module):
#         self.name = "Str"
#         self.type = "Literal"
#         self.ret_type = "str"

#         fmt = "%i \n\0"
#         self.ir_type = ir.Constant(ir.ArrayType(ir.IntType(8), len(value)),
#                             bytearray(fmt.encode("utf8")))
#         self.value = ir.GlobalVariable(module, self.ir_type.type)
#         self.value.linkage = 'internal'
#         self.value.global_constant = True
#         self.value.initializer = self.ir_type
    
#     @staticmethod
#     def convert_from(typ: str, previous):
#         if typ!= 'f64': previous.sitofp(Float_64.ir_type)
        
#         return previous


#     def eval(self, func) -> ir.Constant:
        
#         return ir.Constant(self.ir_type, self.value)

types = {
    'void': Void,
    'bool': Integer_1,
    "i32": Integer_32,
    "int": Integer_32,
    'f64': Float_64,
    'float': Float_64
    # 'string': String_Literal
}

def list_type_conversion(objs: List[AST_NODE]):
    '''When a math operation happens between types, we need to know what the final return type will be.'''
    conversion_priority_raw = ['bool','i32', 'i64', 'f64', 'f128'] # the further down the list this is, the higher priority
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