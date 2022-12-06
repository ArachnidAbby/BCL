from Ast import Ast_Types
from Ast.nodetypes import NodeTypes
from errors import error
from llvmlite import ir

from . import Type_Base


class Char(Type_Base.Type):
    __slots__ = tuple()

    ir_type = ir.IntType(8)
    name = 'char'
    pass_as_ptr = False

    @classmethod
    def convert_from(cls, func, typ, previous):
        if typ.name in ('f32', 'f64'): return func.builder.fptosi(previous.eval(),Char.ir_type)
        elif typ.name == 'bool': return func.builder.zext(previous.eval(), Char.ir_type)
        elif typ.name == 'i64': return func.builder.trunc(previous.eval(), Char.ir_type)
        elif typ.name == 'char': return previous.eval()

        error(f"type '{typ}' cannot be converted to 'i32'",line = previous.position)

    
    def convert_to(self, func, orig, typ):
        match typ.name:
            case 'char': return orig.eval(func)
            case 'bool': return func.builder.trunc(orig.eval(func), ir.IntType(1))
            case 'i32': return func.builder.zext(orig.eval(func), ir.IntType(32))
            case 'i64': return func.builder.zext(orig.eval(func), ir.IntType(64))
            case 'f32': return func.builder.sitofp(orig.eval(func), ir.FloatType())
            case 'f64': return func.builder.sitofp(orig.eval(func), ir.DoubleType())
        
        error(f"Cannot convert 'bool' to '{typ}'", line = orig.position)

    @classmethod
    def get_op_return(cls, op: str, lhs, rhs):
        match op.lower():
            case 'sum'|'sub'|'mul'|'div'|'mod':
                return Type_Base.get_std_ret_type(lhs, rhs)
            case 'eq'|'neq'|'geq'|'leq'|'le'|'gr':
                return Ast_Types.Type_Bool.Integer_1()

    @staticmethod
    def convert_args(func, lhs, rhs) -> tuple:
        typ = Type_Base.get_std_ret_type(lhs, rhs)
        lhs = (lhs.ret_type).convert_to(func, lhs, typ)
        rhs = (rhs.ret_type).convert_to(func, rhs, typ)
        return (lhs, rhs)


    
    def sum(self, func, lhs, rhs): 
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.add(lhs, rhs)

    
    def sub(self, func, lhs, rhs): 
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.sub(lhs, rhs)

    
    def mul(self, func, lhs, rhs): 
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.mul(lhs, rhs)

    
    def div(self, func, lhs, rhs): 
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.sdiv(lhs, rhs)

    
    def mod(self, func, lhs, rhs): 
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.srem(lhs, rhs)



    
    
    def eq(self, func, lhs, rhs): 
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('==', lhs, rhs)
    
    def neq(self, func, lhs, rhs):
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('!=', lhs, rhs)
    
    def geq(self, func, lhs, rhs):
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>=', lhs, rhs)
    
    def leq(self, func, lhs, rhs):
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<=', lhs, rhs)
    
    def le(self, func, lhs, rhs):
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('<', lhs, rhs)
    
    def gr(self, func, lhs, rhs):
        lhs, rhs = Char.convert_args(func, lhs, rhs)
        return func.builder.icmp_signed('>', lhs, rhs)