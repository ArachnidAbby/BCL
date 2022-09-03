from Ast.Ast_Types.Utils import Types
from Ast.Node_Types import NodeTypes
from Errors import error
from llvmlite import ir

from . import Type_Base


class Void(Type_Base.AbstractType):
    __slots__ = tuple()

    ir_type = ir.VoidType()

    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ == Types.VOID: return previous
        else: error(f"type '{typ}' cannot be converted to type 'void'", line = previous.position)

    @staticmethod
    def convert_to(func, orig, typ):
        match typ:
            case Types.VOID: return orig.eval(func)
            case _: error(f"Cannot convert 'void' to type '{typ}'", line = orig.position)

    @staticmethod
    def get_op_return(op: str, lhs, rhs):
        return Types.VOID
