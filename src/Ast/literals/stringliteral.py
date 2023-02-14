from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.literals.numberliteral import Literal
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition


class StrLiteral(ExpressionNode):
    __slots__ = ('value', 'ir_type')
    isconstant = True

    def __init__(self, pos: SrcPosition, value: str):
        super().__init__(pos)
        self.value = value

    def pre_eval(self, func):
        array_size = Literal(SrcPosition.invalid(), len(self.value),
                             Ast_Types.Integer_32)
        self.ret_type = Ast_Types.StringLiteral(array_size)
        self.ir_type = self.ret_type.ir_type

    def eval(self, func) -> ir.Constant:
        encoded_string = self.value.encode("utf-8")
        length = len(encoded_string)
        const = ir.Constant(ir.ArrayType(ir.IntType(8), length),
                            bytearray(encoded_string))
        ptr = func.builder.alloca(ir.ArrayType(ir.IntType(8), length))
        func.builder.store(const, ptr)
        return ptr

    def get_ptr(self, func):
        return func.builder.bitcast(self.eval(func),
                                    ir.IntType(8).as_pointer())
