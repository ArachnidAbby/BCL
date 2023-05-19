from llvmlite import ir

import errors
from Ast.Ast_Types.Type_Base import Type
from Ast.nodes import ExpressionNode

from .Type_Bool import Integer_1
from .Type_Char import Char
from .Type_F32 import Float_32
from .Type_I32 import Integer_32
from .Type_Range import RangeType
from .Type_StrLit import StringLiteral
from .Type_Void import Void

types_dict = {
    'void': Void,
    'bool': Integer_1,
    'char': Char,
    "i32": Integer_32(),
    "int": Integer_32(),
    'i64': Integer_32(64, 'i64',
                      (-9223372036854775808, 9223372036854775807)),
    'f32': Float_32(),
    'f64': Float_32(name='f64', typ=ir.DoubleType()),
    'float': Float_32(),

    'Range': RangeType,
    'strlit': StringLiteral
}

# todo: replace strings in the future
conversion_priority_raw = [
    Type(),
    Integer_1(),
    Char(),
    Integer_32(),
    types_dict['i64'],
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
