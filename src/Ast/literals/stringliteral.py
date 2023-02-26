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
                             Ast_Types.Integer_32())
        self.ret_type = Ast_Types.StringLiteral(array_size)

    def eval(self, func) -> ir.Constant:
        ZERO = ir.Constant(ir.IntType(32), 0)

        encoded_string = self.value.encode("utf-8")
        length = len(encoded_string)
        const = ir.Constant(ir.ArrayType(ir.IntType(8), length),
                            bytearray(encoded_string))
        ptr = func.builder.alloca(ir.ArrayType(ir.IntType(8), length))
        func.builder.store(const, ptr)
        ptr = func.builder.bitcast(ptr, ir.IntType(8).as_pointer())

        string_struct = ir.LiteralStructType((ir.IntType(8).as_pointer(), ))

        val_ptr = func.builder.alloca(string_struct)
        val_str_ptr = func.builder.gep(val_ptr, (ZERO, ZERO))
        func.builder.store(ptr, val_str_ptr)
        val = func.builder.load(val_ptr)

        return val

    # def get_ptr(self, func):
    #     return func.builder.bitcast(self.eval(func),
    #                                 ir.IntType(8).as_pointer())
