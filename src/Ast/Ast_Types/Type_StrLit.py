from typing import Self

from llvmlite import ir  # type: ignore

from Ast.Ast_Types import Type_Char, Type_I32
from errors import error

from . import Type_Base


class StringLiteral(Type_Base.Type):
    __slots__ = ('size', 'typ')
    name = "strlit"
    pass_as_ptr = False
    no_load = False
    returnable = False

    def __init__(self, size=None):
        self.typ = Type_Char.Char()

        if size is not None and not size.isconstant:
            error("size of array type must be a int-literal",
                  line=size.position)

        if size is not None:
            self.size = size.value
            if self.size <= 0:
                error("Array size must be > 0",
                      line=size.position)
            elif size.ret_type != Type_I32.Integer_32:
                error("Array size must be an integer",
                      line=size.position)

        else:
            self.size = size

        self.ir_type = ir.IntType(8).as_pointer()

    @staticmethod
    def convert_from(func, typ: str, previous):
        error(f"type '{typ}' cannot be converted to type 'Array<{typ}>'",
              line=previous.position)

    def convert_to(self, func, orig, typ):
        if typ != self:
            error(f"Cannot convert 'Array<{orig.ir_type.element}>'" +
                  f"to type '{typ}'", line=orig.position)
        return orig.eval(func)

    def get_op_return(self, op, lhs, rhs):
        if op == "ind":
            return self.typ

    # todo: fix indexing
    # def index(self, func, lhs):
    #     return func.builder.load(lhs.get_ptr(func))

    # def put(self, func, lhs, value):
    #     return func.builder.store(value.eval(func), lhs.get_ptr(func))

    def assign(self, func, ptr, value, typ: Self):
        val = value.ret_type.convert_to(func, value, typ)  # type: ignore
        val = func.builder.bitcast(val, self.ir_type)
        func.builder.store(val, ptr.ptr)
