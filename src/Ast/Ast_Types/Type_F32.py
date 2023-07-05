from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.nodes.parenthese import ParenthBlock
from Ast.nodes.passthrough import PassNode
from errors import error

from . import Type_Base, definedtypes


class Float_32(Type_Base.Type):
    __slots__ = ('ir_type', 'name')

    pass_as_ptr = False
    no_load = False

    def __init__(self, name='f32', typ=ir.FloatType()):
        self.ir_type = typ
        self.name = name

    def convert_from(self, func, typ, previous):
        if typ.name in ('i32', 'i64'):
            return func.builder.sitofp(previous.eval(), Float_32.ir_type)
        elif typ.name == 'bool':
            return func.builder.uitofp(previous.eval(), Float_32.ir_type)
        elif typ.name == 'f64':
            return func.builder.fptrunc(previous.eval(), Float_32.ir_type)
        elif typ.name == 'f32' and self.name=="f32":
            return previous.eval(func)

        error(f"type '{typ}' cannot be converted to type 'float'",
              line=previous.position)

    def convert_to(self, func, orig, typ):
        match (typ.name, self.name):
            case ('f32', 'f32'):
                return orig.eval(func)
            case ('f32', 'f64'):
                return func.builder.fptrunc(orig.eval(func), ir.FloatType())
            case ('i8'|'i16'|'i32'|'i64', _):
                return func.builder.fptosi(orig.eval(func), typ.ir_type)
            case ('u8'|'u16'|'u32'|'u64', _):
                return func.builder.fptoui(orig.eval(func), typ.ir_type)
            case ('f64', 'f32'):
                return func.builder.fpext(orig.eval(func), ir.DoubleType())
            case ('f64', 'f64'):
                return orig.eval(func)
            case _: error(f"Cannot convert 'f32' to type '{typ}'",
                          line=orig.position)

    def get_op_return(self, func, op: str, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        match op.lower():
            case 'sum' | 'sub' | 'mul' | 'div' | 'mod'|'pow':
                return definedtypes.get_std_ret_type(lhs, rhs)
            case 'eq' | 'neq' | 'geq' | 'leq' | 'le' | 'gr':
                return Ast_Types.Type_Bool.Integer_1()

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

    def pow(self, func, lhs, rhs):
        desired_typ = definedtypes.get_std_ret_type(lhs, rhs)

        pow_func = func.module.get_global("pow")
        if pow_func is None:
            error("Cannot find 'pow' function in the global namespace.\n" +
                  "Try `import math::*;`",
                  line=lhs.position)
        f64 = Float_32(name="f64", typ=ir.DoubleType())
        arg1 = PassNode(lhs.position, (lhs.ret_type).convert_to(func, lhs, f64), f64)
        arg2 = PassNode(rhs.position, (rhs.ret_type).convert_to(func, rhs, f64), f64)
        args = ParenthBlock(lhs.position)
        args.append_child(arg1)
        args.append_child(arg2)
        args.pre_eval(func)
        output = PassNode(lhs.position, pow_func.call(func, None, args), f64)
        return f64.convert_to(func, output, desired_typ)

    def truthy(self, func, val):
        return func.builder.fcmp_ordered('!=', val.eval(func),
                                         ir.Constant(self.ir_type, float(0.0)))
