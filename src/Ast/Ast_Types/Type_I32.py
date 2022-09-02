from Ast.Node_Types import NodeTypes
from Errors import error
from llvmlite import ir

from . import Type_Base
from . import Utils


class Integer_32(Type_Base.Abstract_Type):
    __slots__ = []

    ir_type = ir.IntType(32)
    
    def init(self, value):
        self.value = value
        self.name = "I32"
        self.type = NodeTypes.EXPRESSION
        self.ret_type = Utils.Types.I32

    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ in (Utils.Types.F64,Utils.Types.F128): return func.builder.fptosi(previous.eval(),Integer_32.ir_type)
        elif typ== Utils.Types.BOOL: return func.builder.zext(previous.eval(), Integer_32.ir_type)
        elif typ == Utils.Types.I64: return func.builder.trunc(previous.eval(), Integer_32.ir_type)
        elif typ == Utils.Types.I32: return previous.eval()

        else: error(f"type '{typ}' cannot be converted to type 'i32'",line = previous.position)

    @staticmethod
    def convert_to(func, orig, typ):
        match typ:
            case Utils.Types.I32: return orig.eval(func)
            case Utils.Types.BOOL: return func.builder.trunc(orig.eval(func), ir.IntType(1))
            case Utils.Types.I64: return func.builder.zext(orig.eval(func), ir.IntType(64))
            case Utils.Types.F64: return func.builder.sitofp(orig.eval(func), ir.FloatType())
            case Utils.Types.F128: return func.builder.sitofp(orig.eval(func), ir.DoubleType())
            case _: error(f"Cannot convert 'i32' to type '{typ}'", line = orig.position)

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)

    @staticmethod
    def get_op_return(op: str, lhs, rhs):
        match op.lower():
            case 'sum'|'sub'|'mul'|'div'|'mod':
                return Type_Base.get_std_ret_type(lhs, rhs)
            case 'eq'|'neq'|'geq'|'leq'|'le'|'gr':
                return Utils.Types.BOOL

    @staticmethod
    def convert_args(func, lhs, rhs) -> tuple:
        typ = Type_Base.get_std_ret_type(lhs, rhs)
        lhs = Type_Base.get_type(lhs.ret_type).convert_to(func, lhs, typ)
        rhs = Type_Base.get_type(rhs.ret_type).convert_to(func, rhs, typ)
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
