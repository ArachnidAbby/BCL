from llvmlite import ir  # type: ignore

from Ast.Ast_Types import Type_F32, Type_I32
from errors import error

from . import Type_Base, definedtypes


class Integer_1(Type_Base.Type):
    __slots__ = ()

    ir_type = ir.IntType(1)
    name = 'bool'
    pass_as_ptr = False
    rang = (0, 1)
    no_load = False

    @classmethod
    def convert_from(cls, func, typ: str, previous):
        if typ in (Type_I32.Integer_32(), Type_F32.Float_32()):
            return func.builder.trunc(previous, Integer_1.ir_type)
        elif typ == Integer_1:
            return previous
        else:
            error(f"type '{typ}' cannot be converted to type 'bool'",
                  line=previous.position)

    def convert_to(self, func, orig, typ):
        match typ:
            case Integer_1():
                return orig.eval(func)
            case Type_I32.Integer_32():
                return func.builder.zext(orig.eval(func), ir.IntType(32))
            case Type_I32.Integer_32(name='i64'):
                return func.builder.zext(orig.eval(func), ir.IntType(64))
            case Type_F32.Float_32():
                return func.builder.sitofp(orig.eval(func), ir.FloatType())
            case Type_F32.Float_32(name="f64"):
                return func.builder.sitofp(orig.eval(func), ir.DoubleType())
            case _:
                error(f"Cannot convert 'bool' to type '{typ}'",
                      line=orig.position)

    def get_op_return(self, op: str, lhs, rhs):
        if x := super().get_op_return(op, lhs, rhs):
            return x
        match op.lower():
            case 'sum' | 'sub' | 'mul' | 'div' | 'mod':
                return definedtypes.get_std_ret_type(lhs, rhs)
            case 'eq' | 'neq' | 'geq' | 'leq' | 'le' | 'gr':
                return Integer_1()

    @staticmethod
    def convert_args(func, lhs, rhs, override_bool=False) -> tuple:
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if override_bool and typ == Integer_1():
            typ = Type_I32.Integer_32()

        lhs = (lhs.ret_type).convert_to(func, lhs, typ)
        rhs = (rhs.ret_type).convert_to(func, rhs, typ)
        return (lhs, rhs)

    def sum(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.sum(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.add(lhs, rhs)

    def sub(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.sub(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.sub(lhs, rhs)

    def mul(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.mul(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.mul(lhs, rhs)

    def div(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.div(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.sdiv(lhs, rhs)

    def mod(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.mod(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.srem(lhs, rhs)

    def eq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if definedtypes.get_std_ret_type(lhs, rhs) != self:
            return typ.eq(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('==', lhs, rhs)

    def neq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if definedtypes.get_std_ret_type(lhs, rhs) != self:
            return typ.neq(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('!=', lhs, rhs)

    def geq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.geq(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>=', lhs, rhs)

    def leq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.leq(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<=', lhs, rhs)

    def le(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.le(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<', lhs, rhs)

    def gr(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.gr(func, lhs, rhs)
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>', lhs, rhs)

    @staticmethod
    def err_if_not_bool(rhs):
        if rhs.ret_type.name != 'bool':
            error('rhs of boolean operation must be of boolean type.',
                  line=rhs.position)

    # def _and(self, func, lhs, rhs):
    #     Integer_1.err_if_not_bool(rhs)
    #     return func.builder.and_(lhs.eval(func), rhs.eval(func))

    # def _or(self, func, lhs, rhs):
    #     Integer_1.err_if_not_bool(rhs)
    #     return func.builder.or_(lhs.eval(func), rhs.eval(func))

    # def _not(self, func, rhs):
    #     Integer_1.err_if_not_bool(rhs)
    #     return func.builder.not_(rhs.eval(func))

    def truthy(self, func, val):
        return val.eval(func)
