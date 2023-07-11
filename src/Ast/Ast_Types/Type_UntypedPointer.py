from llvmlite import ir

import errors
from Ast.Ast_Types.Type_Base import Type
from Ast.Ast_Types.Type_Reference import Reference


class UntypedPointer(Type):
    name = 'UntypedPointer'
    ir_type: ir.Type = ir.IntType(8).as_pointer()

    no_load = True
    read_only = True
    returnable = True
    needs_dispose = True
    ref_counted = True
    generate_bounds_check = False

    def convert_to(self, func, orig, typ):
        if self.roughly_equals(typ):
            return func.builder.bitcast(orig.eval(func), typ.ir_type)

        print(typ)
        errors.error("Cannot convert UntypedPointer to non-pointer type",
                     line=orig.position)

    def get_op_return(self, func, op, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        if op == "ind":
            return self

    def roughly_equals(self, other):
        return isinstance(other, Reference) or self == other

    def index(self, func, lhs):
        return lhs.get_ptr(func)

    def pass_to(self, func, item):
        if item.ret_type == self:
            return item.eval(func)

        return func.builder.bitcast(item.eval(func), self.ir_type)
