from llvmlite import ir

from Ast import Ast_Types
from errors import error

from . import Type_Base, definedtypes


class Float_32(Type_Base.Type):
    __slots__ = ()

    ir_type = ir.FloatType()
    name = 'f32'
    pass_as_ptr = False
    no_load = False

    @classmethod
    def convert_from(cls, func, typ, previous):
        if typ.name in ('i32', 'i64'):
            return func.builder.sitofp(previous.eval(), Float_32.ir_type)
        elif typ.name == 'bool':
            return func.builder.uitofp(previous.eval(), Float_32.ir_type)
        elif typ.name == 'f64':
            return func.builder.fptrunc(previous.eval(), Float_32.ir_type)
        elif typ == 'f32':
            return previous.eval(func)

        error(f"type '{typ}' cannot be converted to type 'float'",
              line=previous.position)

    def convert_to(self, func, orig, typ):
        match typ.name:
            case 'f32':
                return orig.eval(func)
            case 'i32':
                return func.builder.fptosi(orig.eval(func), ir.IntType(32))
            case 'i64':
                return func.builder.fptosi(orig.eval(func), ir.IntType(64))
            case 'f64':
                return func.builder.fpext(orig.eval(func), ir.DoubleType())
            case _: error(f"Cannot convert 'f32' to type '{typ}'",
                          line=orig.position)

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
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fadd(lhs, rhs)

    def sub(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.sub(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fsub(lhs, rhs)

    def mul(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.mul(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fmul(lhs, rhs)

    def div(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.div(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fdiv(lhs, rhs)

    def mod(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.mod(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.frem(lhs, rhs)

    def eq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.eq(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('==', lhs, rhs)

    def neq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.neq(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('!=', lhs, rhs)

    def geq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.geq(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('>=', lhs, rhs)

    def leq(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.leq(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('<=', lhs, rhs)

    def le(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.le(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('<', lhs, rhs)

    def gr(self, func, lhs, rhs):
        typ = definedtypes.get_std_ret_type(lhs, rhs)
        if typ != self:
            return typ.gr(func, lhs, rhs)
        lhs, rhs = Float_32.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('>', lhs, rhs)
