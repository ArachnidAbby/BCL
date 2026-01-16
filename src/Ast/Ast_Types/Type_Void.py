from llvmlite import ir  # type: ignore

from errors import error

from . import Type_Base


class Void(Type_Base.Type):
    __slots__ = ()

    ir_type = ir.VoidType()
    name = 'void'
    pass_as_ptr = False
    no_load = False

    def get_abi_size(self, mod) -> int:
        return 0

    @classmethod
    def convert_from(cls, func, typ: str, previous):
        print("GOT HERE SOMEHOW")
        if typ == Void():
            return previous
        else:
            error(f"type '{typ}' cannot be converted to type 'void'",
                  line=previous.position)

    def convert_to(self, func, orig, typ):
        from Ast.Ast_Types.Type_Union import Union
        if isinstance(typ, Union):
            return typ.convert_from(func, self, orig)

        match typ:
            case Void(): return orig.eval(func)
            case _: error(f"Cannot convert 'void' to type '{typ.__str__()}'",
                          line=orig.position)

    def is_void(self) -> bool:
        return True

    def get_op_return(self, func, op: str, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        return Void()

    def assign(self, func, ptr, value, typ,
               first_assignment=False):
        if typ != self:
            error(f"type '{typ.__str__()}' cannot be converted to type 'void'",
                  line=value.position)
        return  # * we don't actually want to do anything!

