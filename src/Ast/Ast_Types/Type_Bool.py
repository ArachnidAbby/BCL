from Ast.Node_Types import NodeTypes
from Errors import error
from llvmlite import ir

from . import Type_Base
from . import Utils


class Integer_1(Type_Base.Abstract_Type):
    __slots__ = []

    ir_type = ir.IntType(1)
    
    def init(self, value):
        self.value = value
        self.name = "I1"
        self.type = NodeTypes.EXPRESSION
        self.ret_type = Utils.Types.BOOL

    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ in (Utils.Types.I32, Utils.Types.I64): return func.builder.trunc(previous,Integer_1.ir_type)
        elif typ == Utils.Types.BOOL: return previous
        else: error(f"type '{typ}' cannot be converted to type 'bool'", line = previous.position)

    @staticmethod
    def convert_to(func, orig, typ):
        match typ:
            case Utils.Types.BOOL: return orig.eval(func)
            case Utils.Types.I32: return func.builder.zext(orig.eval(func), ir.IntType(32))
            case Utils.Types.I64: return func.builder.zext(orig.eval(func), ir.IntType(64))
            case Utils.Types.F64: return func.builder.sitofp(orig.eval(func), ir.FloatType())
            case Utils.Types.F128: return func.builder.sitofp(orig.eval(func), ir.DoubleType())
            case _: error(f"Cannot convert 'bool' to type '{typ}'", line = orig.position)

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)

    @staticmethod
    def get_op_return(op: str, lhs, rhs):
        match op.lower():
            case 'sum'|'sub'|'mul'|'div'|'mod':
                return Type_Base.get_std_ret_type(lhs, rhs)
            case 'eq'|'neq'|'geq'|'leq'|'le'|'gr'|'and'|'or'|'not':
                return Utils.Types.BOOL

    @staticmethod
    def convert_args(func, lhs, rhs, override_bool = False) -> tuple:
        typ = Type_Base.get_std_ret_type(lhs, rhs)
        if override_bool and typ==Utils.Types.BOOL: typ = Utils.Types.I32
        
        lhs = Type_Base.get_type(lhs.ret_type).convert_to(func, lhs, typ)
        rhs = Type_Base.get_type(rhs.ret_type).convert_to(func, rhs, typ)
        return (lhs, rhs)


    @staticmethod
    def sum(func, lhs, rhs): 
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs, True)
        return func.builder.add(lhs, rhs)

    @staticmethod
    def sub(func, lhs, rhs): 
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs, True)
        return func.builder.sub(lhs, rhs)

    @staticmethod
    def mul(func, lhs, rhs): 
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs, True)
        return func.builder.mul(lhs, rhs)

    @staticmethod
    def div(func, lhs, rhs): 
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs, True)
        return func.builder.sdiv(lhs, rhs)

    @staticmethod
    def mod(func, lhs, rhs): 
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs, True)
        return func.builder.srem(lhs, rhs)



    
    @staticmethod
    def eq(func, lhs, rhs): 
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('==', lhs, rhs)
    @staticmethod
    def neq(func, lhs, rhs):
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('!=', lhs, rhs)
    @staticmethod
    def geq(func, lhs, rhs):
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>=', lhs, rhs)
    @staticmethod
    def leq(func, lhs, rhs):
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<=', lhs, rhs)
    @staticmethod
    def le(func, lhs, rhs):
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<', lhs, rhs)
    @staticmethod
    def gr(func, lhs, rhs):
        lhs, rhs = Integer_1.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>', lhs, rhs)

    @staticmethod
    def err_if_not_bool(rhs):
        if rhs.ret_type != 'bool':
            error('rhs of boolean operation must be of boolean type.', line = rhs.position)

    @staticmethod
    def _and(func, lhs, rhs):
        Integer_1.err_if_not_bool(rhs)
        return func.builder.and_(lhs.eval(func), rhs.eval(func))
    @staticmethod
    def _or(func, lhs, rhs):
        Integer_1.err_if_not_bool(rhs)
        return func.builder.or_(lhs.eval(func), rhs.eval(func))
    @staticmethod
    def _not(func, rhs):
        Integer_1.err_if_not_bool(rhs)
        return func.builder.not_(rhs.eval(func))
