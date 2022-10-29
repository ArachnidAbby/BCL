# from Ast import Ast_Types
from Ast.nodetypes import NodeTypes
from errors import error
from llvmlite import ir

from . import Type_Base


class Void(Type_Base.AbstractType):
    __slots__ = tuple()

    ir_type = ir.VoidType()
    name = 'void'

    @classmethod
    def convert_from(cls, func, typ: str, previous):
        if typ == Void(): return previous
        else: error(f"type '{typ}' cannot be converted to type 'void'", line = previous.position)

    def convert_to(self, func, orig, typ):
        match typ:
            case Void(): return orig.eval(func)
            case _: error(f"Cannot convert 'void' to type '{typ}'", line = orig.position)


    def get_op_return(self, op: str, lhs, rhs):
        return Void()
