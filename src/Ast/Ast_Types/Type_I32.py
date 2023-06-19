from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.Ast_Types import definedtypes
from errors import error

from . import Type_Base


# TODO: Refactor this class name
# Its a pain in the ass so do it when there is downtime.
class Integer_32(Type_Base.Type):
    __slots__ = ('ir_type', 'name', 'rang', 'signed', 'size')

    pass_as_ptr = False
    no_load = False

    def __init__(self, size=32, name='i32', rang=(-2147483648, 2147483647), signed=True):
        self.name = name
        self.size = size
        self.signed = signed
        self.ir_type = ir.IntType(size)
        self.rang = rang

    def __call__(self):
        return self

    def convert_from(self, func, typ, previous):
        if typ.name in ('f32', 'f64'):
            return func.builder.fptosi(previous.eval(func), self.ir_type)
        elif typ.name == 'bool':
            return func.builder.zext(previous.eval(func), self.ir_type)
        elif typ.name == 'i64':
            return func.builder.trunc(previous.eval(func), self.ir_type)
        elif typ.name == 'i32':
            return previous.eval(func)

        error(f"type '{typ}' cannot be converted to type 'i32'",
              line=previous.position)

    def convert_to(self, func, orig, typ):
        if typ == self:
            return orig.eval(func)

        if isinstance(typ, Integer_32):
            if typ.size == self.size:
                return orig.eval(func)
            if typ.size < self.size:
                return func.builder.trunc(orig.eval(func), typ.ir_type)
            if typ.size > self.size:
                if typ.signed:
                    return func.builder.sext(orig.eval(func), typ.ir_type)
                return func.builder.zext(orig.eval(func), typ.ir_type)

        match (typ.name, self.name):
            case ('char', 'i8'):
                return orig.eval(func)
            case ('bool', _):
                return func.builder.trunc(orig.eval(func), ir.IntType(1))
            case ('char', _):
                return func.builder.trunc(orig.eval(func), ir.IntType(8))
            case ('f32', _):
                if not self.signed:
                    return func.builder.uitofp(orig.eval(func), ir.FloatType())
                return func.builder.sitofp(orig.eval(func), ir.FloatType())
            case ('f64', _):
                if not self.signed:
                    return func.builder.uitofp(orig.eval(func), ir.DoubleType())
                return func.builder.sitofp(orig.eval(func), ir.DoubleType())

        error(f"Cannot convert 'i32' to type '{typ}'", line=orig.position)

    @classmethod
    def get_op_return(cls, op: str, lhs, rhs):
        match op.lower():
            case 'sum' | 'sub' | 'mul' | 'div' | 'mod':
                return definedtypes.get_std_ret_type(lhs, rhs)
            case 'eq' | 'neq' | 'geq' | 'leq' | 'le' | 'gr':
                return Ast_Types.Type_Bool.Integer_1()

    @staticmethod
    def convert_args(func, lhs, rhs) -> tuple:
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        lhs = (lhs.ret_type).convert_to(func, lhs, typ)
        rhs = (rhs.ret_type).convert_to(func, rhs, typ)
        return (lhs, rhs)

    def sum(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.sum(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.add(lhs, rhs)

    def sub(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.sub(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.sub(lhs, rhs)

    def mul(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.mul(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.mul(lhs, rhs)

    def div(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.div(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.sdiv(lhs, rhs)

    def mod(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.mod(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.srem(lhs, rhs)

    def eq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.eq(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('==', lhs, rhs)

    def neq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.neq(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('!=', lhs, rhs)

    def geq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.geq(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>=', lhs, rhs)

    def leq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.leq(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<=', lhs, rhs)

    def le(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.le(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<', lhs, rhs)

    def gr(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.gr(func, lhs, rhs)
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>', lhs, rhs)

    def truthy(self, func, val):
        return func.builder.icmp_signed('!=', val.eval(func),
                                        ir.Constant(self.ir_type, int(0)))
