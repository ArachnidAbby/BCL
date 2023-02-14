from Ast import Ast_Types
from Ast.reference import Ref
from errors import error

from . import Type_Base


class Reference(Type_Base.Type):
    __slots__ = ("typ", )

    name = 'ref'
    pass_as_ptr = False
    no_load = True
    returnable = False

    def __init__(self, typ):
        self.typ = typ

        self.ir_type = typ.ir_type.as_pointer()

    def __eq__(self, other):
        return self.name == other.name and self.typ == other.typ

    def __neq__(self, other):
        return self.name != other.name or self.typ != other.typ

    def __str__(self) -> str:
        return f'&{str(self.typ)}'

    def __hash__(self):
        return hash(f"&{self.typ}")

    def convert_from(self, func, typ, previous):
        if typ.name == "ref" and isinstance(previous.ret_type, Ref):
            error("Pointer conversions are not supported due to unsafe " +
                  "behavior", line=previous.position)
        return self.typ.convert_from(func, typ, previous)

    def convert_to(self, func, orig, typ):
        if typ.name == "ref" or typ == self.typ:
            return orig.eval(func)
        error("Pointer conversions are not supported due to unsafe behavior",
              line=orig.position)

    def get_op_return(self, op: str, lhs, rhs):
        self.typ.get_op_return(op, lhs, rhs)

    def sum(self, func, lhs, rhs):
        return lhs.typ.sum(func, lhs.as_varref(), rhs)

    def sub(self, func, lhs, rhs):
        return lhs.typ.sub(func, lhs.as_varref(), rhs)

    def mul(self, func, lhs, rhs):
        return lhs.typ.mul(func, lhs.as_varref(), rhs)

    def div(self, func, lhs, rhs):
        return lhs.typ.div(func, lhs.as_varref(), rhs)

    def mod(self, func, lhs, rhs):
        return lhs.typ.mod(func, lhs.as_varref(), rhs)

    def eq(self, func, lhs, rhs):
        return lhs.typ.eq(func, lhs.as_varref(), rhs)

    def neq(self, func, lhs, rhs):
        return lhs.typ.neq(func, lhs.as_varref(), rhs)

    def geq(self, func, lhs, rhs):
        return lhs.typ.geq(func, lhs.as_varref(), rhs)

    def leq(self, func, lhs, rhs):
        return lhs.typ.leq(func, lhs.as_varref(), rhs)

    def le(self, func, lhs, rhs):
        return lhs.typ.le(func, lhs.as_varref(), rhs)

    def gr(self, func, lhs, rhs):
        return lhs.typ.gr(func, lhs.as_varref(), rhs)

    def assign(self, func, ptr, value, typ: Ast_Types.Type):
        val = value.ret_type.convert_to(func, value, typ.typ)  # type: ignore
        func.builder.store(val, ptr)
