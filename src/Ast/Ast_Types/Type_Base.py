from enum import Enum
from typing import Self

from llvmlite import ir

from Ast.nodes import ASTNode, ExpressionNode
from errors import error


class Type:
    '''abstract type class that outlines the necessary features of a type class.'''

    __slots__ =('ir_type')
    name = "UNKNOWN"
    pass_as_ptr = False
    rang: tuple[int, int]|None = None # Used for optimizations in array indexing. This is pretty epic.
    no_load = False # when allocating arguments as local vars on the stack this is checked -- False: Do allocated and load, True: Don't
    read_only = False # useful for things like function types. 
    has_members = False
    returnable = True # is this type allowed to be the return type of a function

    def __init__(self):
        pass

    @classmethod
    def convert_from(cls, func, typ, previous) -> ir.Instruction: error(f"Type has no conversions",  line=previous.position)
    
    def convert_to(self, func, orig, typ) -> ir.Instruction: error(f"Type has no conversions",  line=orig.position)

    def is_void(self) -> bool:
        return self.name == "void"
    
    def get_member(self, func, lhs, name) -> tuple[ir.Instruction, Self]|None:
        return None

    def __eq__(self, other):
        return (other is not None) and self.name == other.name
    def __neq__(self, other):
        return other is None or self.name != other.name
    
    def get_op_return(self, op, lhs, rhs): pass

    def sum(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '+' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def sub(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '-' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def mul(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '*' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def div(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '/' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def mod(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '%' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def pow(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '**' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def eq(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '==' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def neq(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '!=' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def geq(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '>=' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def leq(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def le(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def gr(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line=lhs.position)
    
    def _not(self, func, rhs) -> ir.Instruction:
        error(f"Operator 'not' is not supported for type '{rhs.ret_type}'", line=rhs.position)

    def _and(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator 'and' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def _or(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator 'or' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def index(self, func, lhs) -> ir.Instruction:
        error(f"Operation 'index' is not supported for type '{lhs.ret_type}'", line=lhs.position)
    def put(self, func, lhs, value):
        error(f"Operation 'putat' is not supported for type '{lhs.ret_type}'", line=lhs.position)

    def call(self, func, lhs, args) -> ir.Instruction:
        error(f"type '{lhs.ret_type}' is not Callable", line=lhs.position)

    def assign(self, func, ptr, value, typ: Self):
        if self.read_only:
            error("This type is read_only", line=value.position, full_line=True)
        val = value.ret_type.convert_to(func, value, typ)  # type: ignore
        func.builder.store(val, ptr.ptr)

    def isum(self, func, ptr, rhs):
        final_value = self.sum(func, ptr, rhs)
        ptr = ptr.get_ptr(func)
        func.builder.store(final_value, ptr)

    def isub(self, func, ptr, rhs):
        final_value = self.sub(func, ptr, rhs)
        ptr = ptr.get_ptr(func)
        func.builder.store(final_value, ptr)

    def imul(self, func, ptr, rhs):
        final_value = self.mul(func, ptr, rhs)
        ptr = ptr.get_ptr(func)
        func.builder.store(final_value, ptr)

    def idiv(self, func, ptr, rhs):
        final_value = self.div(func, ptr, rhs)
        ptr = ptr.get_ptr(func)
        func.builder.store(final_value, ptr)

    def __hash__(self):
        return hash(self.name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}>'

    def __str__(self) -> str:
        return self.name

    def eval(self, foo): #? Why is this here
        '''Does nothing'''
        pass

    def as_type_reference(self):
        return self

    def get_members(self):
        '''Gets all the member names.
           Must check `typ.has_members` or an Exception will occur
        '''
        return self.members.keys()  # members should always be a dict!


from .Type_Bool import Integer_1
from .Type_Char import Char
from .Type_F32 import Float_32
from .Type_I32 import Integer_32
from .Type_StrLit import StringLiteral
from .Type_Void import Void

types_dict = {
    'void': Void,
    'bool': Integer_1,
    'char': Char,
    "i32": Integer_32,
    "int": Integer_32,
    'f32': Float_32,
    'float': Float_32,
    'strlit': StringLiteral
}

# todo: replace strings in the future
conversion_priority_raw = [
    Type(),
    Integer_1(),
    Char(),
    Integer_32(),
    'i64',
    Float_32(),
    'f64'
] # the further down the list this is, the higher priority
conversion_priority = {x: c for c,x in enumerate(conversion_priority_raw)}

def get_std_ret_type(self: ExpressionNode, other: ExpressionNode):
    '''When a math operation happens between types, we need to know what the final return type will be.'''
    largest_priority = max(
        conversion_priority[self.ret_type],
        conversion_priority[other.ret_type]
    )

    return conversion_priority_raw[largest_priority]
