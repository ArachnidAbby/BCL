from Ast.Node_Types import NodeTypes
from Errors import error
from llvmlite import ir

from . import Type_Base


class Array(Type_Base.AbstractType):
    __slots__ = ('size', 'typ')

    def __init__(self, size, typ, default_value):
        self.ir_type = ir.ArrayType(typ.ir_type, size)
        self.size = size
        self.typ = typ # elements' type

    @staticmethod
    def convert_from(func, typ: str, previous):
        error(f"type '{typ}' cannot be converted to type 'Array<{typ}>'", line = previous.position)

    def convert_to(self, func, orig, typ):
        error(f"Cannot convert 'Array<{orig.ir_type.element}>' to type '{typ}'", line = orig.position)
    
    def get_op_return(self, op, lhs, rhs):
        if op == "ind":
            return self.typ

    def index(self, func, lhs, rhs):
        if lhs.ir_type.count < rhs.value: error(f'Array index out range. Max size \'{lhs.ir_type.count}\'', line = lhs.position)
        return func.builder.extract_value(lhs.eval(), rhs.eval())
    
    def put(self, func, lhs, rhs, value):
        if lhs.ir_type.count < rhs.value: error(f'Array index out range. Max size \'{lhs.ir_type.count}\'', line = lhs.position)
        return func.builder.insert_value(lhs.eval(), value.eval(), rhs.eval())
