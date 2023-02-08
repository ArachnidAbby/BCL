from Ast.Ast_Types.Type_Base import Type
from Ast.nodes import ExpressionNode

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
]  # the further down the list this is, the higher priority
conversion_priority = {x: c for c, x in enumerate(conversion_priority_raw)}


def get_std_ret_type(self: ExpressionNode, other: ExpressionNode):
    '''When a math operation happens between types,
    we need to know what the final return type will be.'''
    largest_priority = max(
        conversion_priority[self.ret_type],
        conversion_priority[other.ret_type]
    )

    return conversion_priority_raw[largest_priority]
