from llvmlite import ir  # type: ignore

from errors import error

from . import Type_Base


class Void(Type_Base.Type):
    __slots__ = ()

    ir_type = ir.VoidType()
    name = 'void'
    pass_as_ptr = False
    no_load = False

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
            case _: error(f"Cannot convert 'void' to type '{typ}'",
                          line=orig.position)

    def is_void(self) -> bool:
        return True

    def get_op_return(self, op: str, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        return Void()
