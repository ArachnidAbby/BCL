from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.literals.numberliteral import Literal
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import Lifetimes, SrcPosition


class StrLiteral(ExpressionNode):
    __slots__ = ('value', 'ir_type')
    isconstant = True

    def __init__(self, pos: SrcPosition, value: str):
        super().__init__(pos)
        self.value = value

    def copy(self):
        return StrLiteral(self._position, self.value)

    def fullfill_templates(self, func):
        return super().fullfill_templates(func)

    def pre_eval(self, func):
        array_size = Literal(SrcPosition.invalid(), len(self.value),
                             Ast_Types.Integer_32())
        self.ret_type = Ast_Types.definedtypes.types_dict['strlit']

    def get_lifetime(self, func):
        return Lifetimes.FUNCTION

    def eval_impl(self, func) -> ir.Constant:
        ZERO = ir.Constant(ir.IntType(32), 0)


        encoded_string = self.value.encode("utf-8")
        length = len(encoded_string)


        string_actual_typ = ir.LiteralStructType((ir.IntType(64),
                                                  ir.ArrayType(ir.IntType(8),
                                                               length),))


        const = ir.Constant(ir.ArrayType(ir.IntType(8), length),
                            bytearray(encoded_string))
        # ptr = func.builder.alloca(ir.ArrayType(ir.IntType(8), length+8))
        ptr = func.builder.alloca(string_actual_typ)

        size_ptr = func.builder.gep(ptr, (ZERO, ZERO))

        str_ptr = func.builder.gep(ptr, (ZERO, ir.Constant(ir.IntType(32), 1)))

        # Don't count the null character in the length
        func.builder.store(ir.Constant(ir.IntType(64), length-1), size_ptr)

        func.builder.store(const, str_ptr)
        ptr = func.builder.bitcast(str_ptr, ir.IntType(8).as_pointer())

        string_struct = ir.LiteralStructType((ir.IntType(8).as_pointer(), ))

        val_ptr = func.builder.alloca(string_struct)
        val_str_ptr = func.builder.gep(val_ptr, (ZERO, ZERO))
        func.builder.store(ptr, val_str_ptr)
        val = func.builder.load(val_ptr)

        return val

    def repr_as_tree(self) -> str:
        return self.create_tree("String Literal",
                                content=self.value,
                                return_type=self.ret_type)

    def __str__(self) -> str:
        # Don't include the null character
        return '"' + self.value[0:-1] + '"'
