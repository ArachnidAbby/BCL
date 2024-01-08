from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.Ast_Types import definedtypes
from Ast.Ast_Types.Type_Alias import Alias
from Ast.nodes.parenthese import ParenthBlock
from Ast.nodes.passthrough import PassNode
from errors import error

from . import Type_Base

# Ranges
U8_RANGE = (0, 255)
U16_RANGE = (0, 65535)
U32_RANGE = (0, 4294967295)
U64_RANGE = (0, 18446744073709551615)

I8_RANGE = (-128, 127)
I16_RANGE = (-32768, 32767)
I32_RANGE = (-2147483648, 2147483647)
I64_RANGE = (-9223372036854775808, 9223372036854775807)


# TODO: Refactor this class name
# Its a pain in the ass so do it when there is downtime.
class Integer_32(Type_Base.Type):
    __slots__ = ('ir_type', 'name', 'rang', 'signed', 'size')

    pass_as_ptr = False
    no_load = False
    needs_dispose = False

    def __init__(self, size=32, name='i32', rang=I32_RANGE, signed=True):
        self.name = name
        self.size = size
        self.signed = signed
        self.ir_type = ir.IntType(size)
        self.rang = rang

    def __call__(self):
        return self

    def get_namespace_name(self, func, name, pos):
        from Ast.module import NamespaceInfo
        if x := self.global_namespace_names(func, name, pos):
            return x

        from Ast.literals.numberliteral import Literal
        if name == "MAX":
            val = Literal(pos, self.rang[1], self)
            return NamespaceInfo(val, {})

        if name == "MIN":
            val = Literal(pos, self.rang[0], self)
            return NamespaceInfo(val, {})

        error(f"Name \"{name}\" cannot be " +
              f"found in Type \"{str(self)}\"",
              line=pos)

    def bitwise_op_check(self, func, other, symbol):
        if not isinstance(other.ret_type, Integer_32):
            error(f"Right hand side of '{symbol}'operation must be an integer",
                  line=other.position)

        return other.ret_type.convert_to(func, other, self)

    # def convert_from(self, func, typ, previous):
    #     if typ.name in ('f32', 'f64'):
    #         return func.builder.fptosi(previous.eval(func), self.ir_type)
    #     elif typ.name == 'bool':
    #         return func.builder.zext(previous.eval(func), self.ir_type)
    #     elif typ.name == 'i64':
    #         return func.builder.trunc(previous.eval(func), self.ir_type)
    #     elif typ.name == 'i32':
    #         return previous.eval(func)

    #     error(f"type '{typ}' cannot be converted to type 'i32'",
    #           line=previous.position)

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
            # case ('char', 'i8'):
            #     return orig.eval(func)
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

    def roughly_equals(self, other):
        return (isinstance(other, Integer_32) or
                (isinstance(other, Alias) and isinstance(other.aliased_typ, Integer_32))) and \
               self.size == other.size and self.signed == other.signed

    def get_op_return(self, func, op: str, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        match op.lower():
            case 'sum' | 'sub' | 'mul' | 'div' | 'mod' | 'pow':
                return definedtypes.get_std_ret_type(lhs, rhs)
            case 'eq' | 'neq' | 'geq' | 'leq' | 'le' | 'gr':
                return Ast_Types.Type_Bool.Integer_1()
            case 'lshift' | 'rshift' | 'bor' | 'bxor' | 'band' | 'bitnot':
                return lhs.ret_type

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

    def lshift(self, func, lhs, rhs):
        rhs_eval = self.bitwise_op_check(func, rhs, '<<')
        lhs_eval = lhs.eval(func)
        return func.builder.shl(lhs_eval, rhs_eval)

    def rshift(self, func, lhs, rhs):
        rhs_eval = self.bitwise_op_check(func, rhs, '<<')
        lhs_eval = lhs.eval(func)
        return func.builder.lshr(lhs_eval, rhs_eval)

    def bit_or(self, func, lhs, rhs):
        rhs_eval = self.bitwise_op_check(func, rhs, '|')
        lhs_eval = lhs.eval(func)
        return func.builder.or_(lhs_eval, rhs_eval)

    def bit_xor(self, func, lhs, rhs):
        rhs_eval = self.bitwise_op_check(func, rhs, '^')
        lhs_eval = lhs.eval(func)
        return func.builder.xor(lhs_eval, rhs_eval)

    def bit_and(self, func, lhs, rhs):
        rhs_eval = self.bitwise_op_check(func, rhs, '&')
        lhs_eval = lhs.eval(func)
        return func.builder.and_(lhs_eval, rhs_eval)

    def bit_not(self, func, lhs, rhs):
        lhs_eval = lhs.eval(func)
        return func.builder.not_(lhs_eval)

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

    def pow(self, func, lhs, rhs):
        desired_typ = definedtypes.get_std_ret_type(lhs, rhs)
        if desired_typ != self:
            return desired_typ.pow(func, lhs, rhs)

        pow_func = func.module.get_global("pow")
        if pow_func is None:
            error("Cannot find 'pow' function in the global namespace.\n" +
                  "Try `import math::*;`",
                  line=lhs.position)
        pow_func = pow_func.obj
        i64 = Integer_32(name="i64", size=64)
        i32 = Integer_32(name="i32", size=32)
        arg1 = PassNode(lhs.position, (lhs.ret_type).convert_to(func, lhs, i64), i64)
        arg2 = PassNode(rhs.position, (rhs.ret_type).convert_to(func, rhs, i32), i32)
        args = ParenthBlock(lhs.position)
        args.append_child(arg1)
        args.append_child(arg2)
        args.pre_eval(func)
        output = PassNode(lhs.position, pow_func.call(func, None, args), i64)
        return i64.convert_to(func, output, desired_typ)

    def truthy(self, func, val):
        return func.builder.icmp_signed('!=', val.eval(func),
                                        ir.Constant(self.ir_type, 0))
