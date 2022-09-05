from enum import Enum
from Ast.Nodes import AST_NODE
from Errors import error


class AbstractType:
    '''abstract type class that outlines the necessary features of a type class.'''

    __slots__ = ('ir_type')

    @staticmethod
    def convert_from(func, typ, previous): error(f"AbstractType has no conversions",  line = previous.position)
    @staticmethod
    def convert_to(func, orig, typ): error(f"AbstractType has no conversions",  line = orig.position)

    @classmethod
    def print_error(cls, op: str, lhs, rhs):
        if op=='not': cls._not(None, rhs)

        {
            'sum': cls.sum,
            'sub': cls.sub,
            'mul': cls.mul,
            'div': cls.div,
            'mod': cls.mod,
            'eq': cls.eq,
            'neq': cls.neq,
            'geq': cls.geq,
            'leq': cls.leq,
            'le': cls.le,
            'gr': cls.gr,
            'and': cls._and,
            'or': cls._or,
        }[op](None, lhs, rhs)

    @staticmethod
    def get_op_return(op, lhs, rhs): pass


    @staticmethod
    def sum  (func, lhs, rhs): error(f"Operator '+' is not supported for type '{lhs.ret_type}'",  line = lhs.position)
    @staticmethod
    def sub  (func, lhs, rhs): error(f"Operator '-' is not supported for type '{lhs.ret_type}'",  line = lhs.position)
    @staticmethod
    def mul  (func, lhs, rhs): error(f"Operator '*' is not supported for type '{lhs.ret_type}'",  line = lhs.position)
    @staticmethod
    def div  (func, lhs, rhs): error(f"Operator '/' is not supported for type '{lhs.ret_type}'",  line = lhs.position)
    @staticmethod
    def mod  (func, lhs, rhs): error(f"Operator '%' is not supported for type '{lhs.ret_type}'",  line = lhs.position)

    @staticmethod
    def eq   (func, lhs, rhs): error(f"Operator '==' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    @staticmethod
    def neq  (func, lhs, rhs): error(f"Operator '!=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    @staticmethod
    def geq  (func, lhs, rhs): error(f"Operator '>=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    @staticmethod
    def leq  (func, lhs, rhs): error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    @staticmethod
    def le   (func, lhs, rhs): error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    @staticmethod
    def gr   (func, lhs, rhs): error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    @staticmethod
    def _not (func, rhs): error(f"Operator 'not' is not supported for type '{rhs.ret_type}'",line = rhs.position)
    @staticmethod
    def _and (func, lhs, rhs): error(f"Operator 'and' is not supported for type '{lhs.ret_type}'",line = lhs.position)
    @staticmethod
    def _or  (func, lhs, rhs): error(f"Operator 'or' is not supported for type '{lhs.ret_type}'", line = lhs.position)


from .Utils import Types

from .Type_Bool import Integer_1
from .Type_F64 import Float_64
from .Type_I32 import Integer_32
from .Type_Void import Void

# def get_type(typ: Types) -> AbstractType:
#     match typ:
#         case Types.VOID:
#             return Void  # type: ignore
#         case Types.I32|Types.INT:
#             return Integer_32  # type: ignore
#         case Types.F64|Types.FLOAT:
#             return Float_64  # type: ignore
#         case Types.BOOL:
#             return Integer_1  # type: ignore
#         case _:
#             return None  # type: ignore

types_dict = {
    'void': Void,
    'bool': Integer_1,
    "i32": Integer_32,
    "int": Integer_32,
    'f64': Float_64,
    'float': Float_64
}

conversion_priority_raw = [
    Types.UNKNOWN,
    Types.BOOL,
    Types.I32,
    Types.I64,
    Types.F64,
    Types.F128
] # the further down the list this is, the higher priority


def get_std_ret_type(self: AST_NODE,  other: AST_NODE):
    '''When a math operation happens between types, we need to know what the final return type will be.'''
    conversion_priority = {x: c for c,x in enumerate(conversion_priority_raw)}

    largest_priority = max(
        conversion_priority[self.ret_type],
        conversion_priority[other.ret_type]
    )

    return conversion_priority_raw[largest_priority]