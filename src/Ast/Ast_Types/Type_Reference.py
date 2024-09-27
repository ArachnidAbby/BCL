from llvmlite import ir

from Ast import Ast_Types
from Ast.nodes.passthrough import PassNode
from errors import error

from . import Type_Base


def try_deref(node, func):
    if not isinstance(node.ret_type, Reference):
        return node

    ptr = node.eval(func)

    return PassNode(node.position,
                    func.builder.load(ptr),
                    node.ret_type.typ,
                    ptr)


class Reference(Type_Base.Type):
    __slots__ = ("typ", "ir_type", "has_members")

    name = 'ref'
    pass_as_ptr = False
    no_load = False
    returnable = False
    checks_lifetime = True

    def __init__(self, typ):
        self.typ = typ
        # self.needs_dispose = typ.needs_dispose
        # self.ref_counted = typ.ref_counted

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

    # def convert_from(self, func, typ, previous):
    #     if typ.name == "ref" and isinstance(previous.ret_type, Reference):
    #         error("Pointer conversions are not supported due to unsafe " +
    #               "behavior", line=previous.position)
    #     return self.typ.convert_from(func, typ, previous)

    def convert_to(self, func, orig, typ):
        if typ == self:
            return orig.eval(func)

        from Ast.Ast_Types.Type_Union import Union
        if isinstance(typ, Union):
            return typ.convert_from(func, self, orig)

        if typ.name == "UntypedPointer":
            return func.builder.bitcast(orig.eval(func), typ.ir_type)
        if typ == self.typ:  # deref is secondary to casting to UntypedPointer.
            return func.builder.load(orig.get_ptr(func))
        error("Pointer conversions are not directly supported due " +
              "to unsafe behavior",
              line=orig.position)

    def get_op_return(self, func, op: str, lhs, rhs):
        return self.typ.get_op_return(func, op, lhs, rhs)

    def get_member_info(self, lhs, rhs):
        return self.typ.get_member_info(lhs, rhs)

    def get_member(self, func, lhs, member_name_in):
        return self.typ.get_member(func, try_deref(lhs, func), member_name_in)

    def sum(self, func, lhs, rhs):
        return self.typ.sum(func, try_deref(lhs, func), rhs)

    def sub(self, func, lhs, rhs):
        return self.typ.sub(func, try_deref(lhs, func), rhs)

    def mul(self, func, lhs, rhs):
        return self.typ.mul(func, try_deref(lhs, func), rhs)

    def div(self, func, lhs, rhs):
        return self.typ.div(func, try_deref(lhs, func), rhs)

    def mod(self, func, lhs, rhs):
        return self.typ.mod(func, try_deref(lhs, func), rhs)

    def eq(self, func, lhs, rhs):
        return self.typ.eq(func, try_deref(lhs, func), rhs)

    def neq(self, func, lhs, rhs):
        return self.typ.neq(func, try_deref(lhs, func), rhs)

    def geq(self, func, lhs, rhs):
        return self.typ.geq(func, try_deref(lhs, func), rhs)

    def leq(self, func, lhs, rhs):
        return self.typ.leq(func, try_deref(lhs, func), rhs)

    def le(self, func, lhs, rhs):
        return self.typ.le(func, try_deref(lhs, func), rhs)

    def gr(self, func, lhs, rhs):
        return self.typ.gr(func, try_deref(lhs, func), rhs)

    def isum(self, func, lhs, rhs):
        return self.typ.isum(func, try_deref(lhs, func), rhs)

    def isub(self, func, lhs, rhs):
        return self.typ.isub(func, try_deref(lhs, func), rhs)

    def imul(self, func, lhs, rhs):
        return self.typ.imul(func, try_deref(lhs, func), rhs)

    def idiv(self, func, lhs, rhs):
        return self.typ.idiv(func, try_deref(lhs, func), rhs)

    def get_assign_type(self, func, value):
        if value.ret_type.roughly_equals(func, self):
            return self
        else:
            return self.typ

    def assign(self, func, ptr, value, typ: "Ast_Types.Type",
               first_assignment=False):
        if value.ret_type.roughly_equals(func, self):
            func.builder.store(value.eval(func), ptr.get_var(func).ptr)
            return

        actual_ptr = func.builder.load(ptr.get_var(func).ptr)
        val = value.ret_type.convert_to(func, value, typ.typ)  # type: ignore
        node = PassNode(value.position, value._instruction, value.ret_type)
        value.ret_type.add_ref_count(func, node)
        func.builder.store(val, actual_ptr)

    def _add_ref_count(self, func, ptr):
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

    def _dispose(self, func, ptr):
        ptr_ptr = ptr.get_ptr(func)
        val = func.builder.load(ptr_ptr)
        ptr_val = val

        if not isinstance(val.type, ir.PointerType):
            ptr_val = ptr_ptr
            val = ptr_ptr

        node = PassNode(ptr.position, None, self.typ, ptr=ptr_val)
        self.typ.dispose(func, node)

    def get_deref_return(self, func, node):
        return self.typ

    def index(self, func, lhs, rhs):
        # ptr = lhs.get_ptr(func)
        # val = func.builder.load(ptr)

        # varref = PassNode(lhs.position, val, self.typ, ptr=ptr)
        return self.typ.index(func, lhs, rhs)

    def deref(self, func, node):
        ptr = node.eval(func)
        return func.builder.load(ptr)

    def lshift(self, func, lhs, rhs):
        return self.typ.lshift(func, try_deref(lhs, func), rhs)

    def rshift(self, func, lhs, rhs):
        return self.typ.rshift(func, try_deref(lhs, func), rhs)

    def bit_or(self, func, lhs, rhs):
        return self.typ.bit_or(func, try_deref(lhs, func), rhs)

    def bit_xor(self, func, lhs, rhs):
        return self.typ.bit_xor(func, try_deref(lhs, func), rhs)

    def bit_and(self, func, lhs, rhs):
        return self.typ.bit_and(func, try_deref(lhs, func), rhs)

    def bit_not(self, func, lhs):
        return self.typ.bit_not(func, try_deref(lhs, func))
