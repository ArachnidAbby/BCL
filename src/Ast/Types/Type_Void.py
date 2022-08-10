from Errors import error
from llvmlite import ir

from . import Type_Base


class Void(Type_Base.Abstract_Type):
    __slots__ = []

    ir_type = ir.VoidType()
    
    def init(self):
        self.value = 'void'
        self.name = "I1"
        self.type = "Literal"
        self.ret_type = "bool"

    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ == 'void': return previous
        else: error(f"type '{typ}' cannot be converted to type 'void'", line = previous.position)

    @staticmethod
    def convert_to(func, orig, typ):
        match typ:
            case 'void': return orig.eval(func)
            case _: error(f"Cannot convert 'void' to type '{typ}'", line = orig.position)

    def eval(self, func):
        pass

    @staticmethod
    def get_op_return(op: str, lhs, rhs):
        return 'void'
