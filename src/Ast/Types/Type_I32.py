from Errors import error
from llvmlite import ir

from . import Type_Base


class Integer_32(Type_Base.Abstract_Type):
    __slots__ = []

    ir_type = ir.IntType(32)
    
    def init(self, value):
        self.value = value
        self.name = "I32"
        self.type = "Literal"
        self.ret_type = "i32"

    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ in ('f64','f128'): return func.builder.fptosi(previous.eval(),Integer_32.ir_type)
        elif typ== 'bool': return func.builder.zext(previous.eval(), Integer_32.ir_type)
        elif typ == 'i64': return func.builder.trunc(previous.eval(), Integer_32.ir_type)
        elif typ == 'i32': return previous.eval()

        else: error(f"type '{typ}' cannot be converted to type 'i32'",line = previous.position)

    @staticmethod
    def convert_to(func, orig, typ):
        match typ:
            case 'i32': return orig.eval(func)
            case 'bool': return func.builder.trunc(orig.eval(func), ir.IntType(1))
            case 'i64': return func.builder.zext(orig.eval(func), ir.IntType(64))
            case 'f64': return func.builder.sitofp(orig.eval(func), ir.FloatType())
            case 'f128': return func.builder.sitofp(orig.eval(func), ir.DoubleType())
            case _: error(f"Cannot convert 'i32' to type '{typ}'", line = orig.position)

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)

    @staticmethod
    def get_op_return(op: str, lhs, rhs):
        match op.lower():
            case 'sum'|'sub'|'mul'|'div'|'mod':
                return Type_Base.get_std_ret_type(lhs, rhs)
            case 'eq'|'neq'|'geq'|'leq'|'le'|'gr':
                return 'bool'

    @staticmethod
    def convert_args(func, lhs, rhs) -> tuple:
        typ = Type_Base.get_std_ret_type(lhs, rhs)
        lhs = Type_Base.types[lhs.ret_type].convert_to(func, lhs, typ)
        rhs = Type_Base.types[rhs.ret_type].convert_to(func, rhs, typ)
        return (lhs, rhs)


    @staticmethod
    def sum(func, lhs, rhs): 
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.add(lhs, rhs)

    @staticmethod
    def sub(func, lhs, rhs): 
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.sub(lhs, rhs)

    @staticmethod
    def mul(func, lhs, rhs): 
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.mul(lhs, rhs)

    @staticmethod
    def div(func, lhs, rhs): 
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.sdiv(lhs, rhs)

    @staticmethod
    def mod(func, lhs, rhs): 
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.srem(lhs, rhs)



    
    @staticmethod
    def eq(func, lhs, rhs): 
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('==', lhs, rhs)
    @staticmethod
    def neq(func, lhs, rhs):
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('!=', lhs, rhs)
    @staticmethod
    def geq(func, lhs, rhs):
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>=', lhs, rhs)
    @staticmethod
    def leq(func, lhs, rhs):
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<=', lhs, rhs)
    @staticmethod
    def le(func, lhs, rhs):
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<', lhs, rhs)
    @staticmethod
    def gr(func, lhs, rhs):
        lhs, rhs = Integer_32.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>', lhs, rhs)
