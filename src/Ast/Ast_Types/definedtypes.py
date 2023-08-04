import platform

from llvmlite import ir

import errors
from Ast.Ast_Types.Type_Base import Type
from Ast.nodes import ExpressionNode

from .Type_Bool import Integer_1
from .Type_Char import Char
from .Type_F32 import Float_32
from .Type_I32 import I16_RANGE, I64_RANGE, I8_RANGE, U16_RANGE, U32_RANGE, U64_RANGE, U8_RANGE, Integer_32
from .Type_Range import RangeType
from .Type_StrLit import StringLiteral
from .Type_UntypedPointer import UntypedPointer
from .Type_Void import Void

types_dict = {
    'void': Void(),
    'bool': Integer_1(),
    'char': Char(),

    "u8": Integer_32(8, 'u8',
                     U8_RANGE, False),
    "u16": Integer_32(16, 'u16',
                      U16_RANGE, False),
    "u32": Integer_32(32, "u32",
                      U32_RANGE, False),
    'u64': Integer_32(64, 'u64',
                      U64_RANGE, False),

    "i8": Integer_32(8, 'i8',
                     I8_RANGE),
    "i16": Integer_32(16, 'i16',
                      I16_RANGE),
    "i32": Integer_32(),
    "int": Integer_32(),
    'i64': Integer_32(64, 'i64',
                      I64_RANGE),

    'f32': Float_32(),
    'f64': Float_32(name='f64', typ=ir.DoubleType()),
    'float': Float_32(),

    'Range': RangeType,
    'strlit': StringLiteral,

    'UntypedPointer': UntypedPointer()
}

needs_declare = [
]

plat = platform.architecture()[0]
if plat == "32bit":
    errors.developer_info("Size_t = u32")
    types_dict["size_t"] = types_dict["u32"]
if plat == "64bit":
    errors.developer_info("Size_t = u64")
    types_dict["size_t"] = types_dict["u64"]
else:
    errors.error("Platform not supported. Only 64bit and 32bit architectures are supported")

# todo: replace strings in the future
conversion_priority_raw = [
    Type(),
    Integer_1(),
    Char(),
    types_dict['i8'],
    types_dict['i16'],
    types_dict['i32'],
    types_dict['i64'],
    types_dict['u8'],
    types_dict['u16'],
    types_dict['u32'],
    types_dict['u64'],
    Float_32(),
    Float_32(name='f64', typ=ir.DoubleType())
]  # the further down the list this is, the higher priority
conversion_priority = {x: c for c, x in enumerate(conversion_priority_raw)}


def get_std_ret_type(self: ExpressionNode, other: ExpressionNode):
    '''When a math operation happens between types,
    we need to know what the final return type will be.'''
    if other.ret_type not in conversion_priority.keys():
        errors.error("Cannot perform operation with a right " +
                     f"operand of type \"{str(other.ret_type)}\"",
                     line=other.position)
    largest_priority = max(
        conversion_priority[self.ret_type],
        conversion_priority[other.ret_type]
    )

    return conversion_priority_raw[largest_priority]
