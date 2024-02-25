from llvmlite import ir  # type: ignore

from errors import error

from . import Type_Base


class Void(Type_Base.Type):
    __slots__ = ()

    ir_type = ir.VoidType()
    name = 'void'
    pass_as_ptr = False
    no_load = False

    def global_namespace_names(self, func, name, pos):
        from Ast.Ast_Types.Type_I32 import Integer_32
        from Ast.literals.numberliteral import Literal
        if name == "SIZEOF":
            ty = Integer_32(name="u64", size=64, signed=False)
            val = Literal(pos, 0, ty)
            return val

        super().global_namespace_names(func, name, pos)

    @classmethod
    def convert_from(cls, func, typ: str, previous):
        if typ == Void():
            return previous
        else:
            error(f"type '{typ}' cannot be converted to type 'void'",
                  line=previous.position)

    def convert_to(self, func, orig, typ):
        match typ:
            case Void(): return orig.eval(func)
            case _: error(f"Cannot convert 'void' to type '{typ.__str__()}'",
                          line=orig.position)

    def is_void(self) -> bool:
        return True

    def get_op_return(self, func, op: str, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        return Void()
