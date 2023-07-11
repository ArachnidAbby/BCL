from Ast import Ast_Types
from Ast.nodes.passthrough import PassNode
from errors import error
from llvmlite import ir

from . import Type_Base


class Reference(Type_Base.Type):
    __slots__ = ("typ", "ir_type", "has_members", "needs_dispose", "ref_counted")

    name = 'ref'
    pass_as_ptr = False
    no_load = False
    returnable = False

    def __init__(self, typ):
        self.typ = typ
        self.needs_dispose = typ.needs_dispose
        self.ref_counted = typ.ref_counted

        self.ir_type = typ.ir_type.as_pointer()
        self.has_members = self.typ.has_members

    def __eq__(self, other):
        return self.name == other.name and self.typ == other.typ

    def __neq__(self, other):
        return self.name != other.name or self.typ != other.typ

    def __str__(self) -> str:
        return f'&{str(self.typ)}'

    def __hash__(self):
        return hash(f"&{self.typ}")

    def convert_from(self, func, typ, previous):
        if typ.name == "ref" and isinstance(previous.ret_type, Reference):
            error("Pointer conversions are not supported due to unsafe " +
                  "behavior", line=previous.position)
        return self.typ.convert_from(func, typ, previous)

    def convert_to(self, func, orig, typ):
        if typ == self.typ:
            self.add_ref_count(func, orig)
            return func.builder.load(orig.get_ptr(func))
        if typ.name == "UntypedPointer":
            return func.builder.bitcast(orig.eval(func), typ.ir_type)
        error("Pointer conversions are not supported due to unsafe behavior",
              line=orig.position)

    def get_op_return(self, func, op: str, lhs, rhs):
        return self.typ.get_op_return(func, op, lhs, rhs)

    def get_member_info(self, lhs, rhs):
        return self.typ.get_member_info(lhs, rhs)

    def get_member(self, func, lhs, member_name_in):
        return self.typ.get_member(func, lhs.as_varref(), member_name_in)

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

    def get_assign_type(self, func, value):
        if value.ret_type.roughly_equals(self):
            return self
        else:
            return self.typ

    def assign(self, func, ptr, value, typ: "Ast_Types.Type",
               first_assignment=False):
        if value.ret_type.roughly_equals(self):
            func.builder.store(value.eval(func), ptr.get_var(func).ptr)
            return

        actual_ptr = func.builder.load(ptr.get_var(func).ptr)
        val = value.ret_type.convert_to(func, value, typ.typ)  # type: ignore
        func.builder.store(val, actual_ptr)

    def add_ref_count(self, func, ptr):
        if not self.ref_counted:
            return

        ptr_ptr = ptr.get_ptr(func)
        val = func.builder.load(ptr_ptr)
        ptr_val = val

        if not isinstance(val.type, ir.PointerType):
            ptr_val = ptr_ptr
            val = ptr_ptr

        node = PassNode(ptr.position, val, self.typ, ptr_val)
        self.typ.add_ref_count(func, node)

    def dispose(self, func, ptr):
        ptr_ptr = ptr.get_ptr(func)
        val = func.builder.load(ptr_ptr)
        ptr_val = val

        if not isinstance(val.type, ir.PointerType):
            ptr_val = ptr_ptr
            val = ptr_ptr

        node = PassNode(ptr.position, None, self.typ, ptr=ptr_val)
        self.typ.dispose(func, node)
