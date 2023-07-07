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

    def convert_to(self, func, orig, typ):
        if self.roughly_equals(typ):
            return func.builder.bitcast(orig.eval(func), typ.ir_type)

        errors.error("Cannot convert UntypedPointer to non-pointer type",
                     line=orig.position)

    def roughly_equals(self, other):
        return isinstance(other, Reference) or self == other

    def pass_to(self, func, item):
        if item.ret_type == self:
            return item.eval(func)

        return func.builder.bitcast(item.eval(func), self.ir_type)
