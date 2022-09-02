from Ast.Node_Types import NodeTypes
from Errors import error
from llvmlite import ir

from . import Type_Base
from . import Utils


class Float_64(Type_Base.Abstract_Type):
    __slots__ = []

    ir_type = ir.IntType(32)
    
    def init(self, value):
        self.value = value
        self.name = "F64"
        self.type = NodeTypes.EXPRESSION
        self.ret_type = Utils.Types.F64
        
    @staticmethod
    def convert_from(func, typ: str, previous):
        if typ in (Utils.Types.I32, Utils.Types.I64): return func.builder.sitofp(previous,Float_64.ir_type)
        elif typ== Utils.Types.BOOL: return func.builder.uitofp(previous, Float_64.ir_type)
        elif typ == Utils.Types.F128: return func.builder.fptrunc(previous, Float_64.ir_type)
        elif typ == Utils.Types.F64: return previous

        else: error(f"type '{typ}' cannot be converted to type 'float'",line = previous.position)

    @staticmethod
    def convert_to(func, orig, typ):
        match typ:
            case Utils.Types.F64: return orig.eval(func)
            case Utils.Types.I32: return func.builder.sitofp(orig.eval(func), ir.IntType(32))
            case Utils.Types.I64: return func.builder.sitofp(orig.eval(func), ir.IntType(64))
            case Utils.Types.F128: return func.builder.fpext(orig.eval(func), ir.DoubleType())
            case _: error(f"Cannot convert 'f64' to type '{typ}'", line = orig.position)

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
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fadd(lhs, rhs)

    @staticmethod
    def sub(func, lhs, rhs): 
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fsub(lhs, rhs)

    @staticmethod
    def mul(func, lhs, rhs): 
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fmul(lhs, rhs)

    @staticmethod
    def div(func, lhs, rhs): 
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fdiv(lhs, rhs)

    @staticmethod
    def mod(func, lhs, rhs): 
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.frem(lhs, rhs)



    
    @staticmethod
    def eq(func, lhs, rhs): 
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('==', lhs, rhs)
    @staticmethod
    def neq(func, lhs, rhs):
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('!=', lhs, rhs)
    @staticmethod
    def geq(func, lhs, rhs):
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('>=', lhs, rhs)
    @staticmethod
    def leq(func, lhs, rhs):
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('<=', lhs, rhs)
    @staticmethod
    def le(func, lhs, rhs):
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('<', lhs, rhs)
    @staticmethod
    def gr(func, lhs, rhs):
        lhs, rhs = Float_64.convert_args(func, lhs, rhs)
        return func.builder.fcmp_ordered('>', lhs, rhs)
