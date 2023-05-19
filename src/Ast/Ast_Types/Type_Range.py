from llvmlite import ir

from Ast.Ast_Types.Type_Base import Type
from Ast.Ast_Types.Type_I32 import Integer_32
from Ast.nodes.commontypes import MemberInfo


class RangeType(Type):
    __slots__ = ()

    name = "Range"
    has_members = True
    is_iterator = True
    # {START: I32, END: I32, CURRENT: I32}
    ir_type = ir.LiteralStructType((ir.IntType(32),
                                    ir.IntType(32),
                                    ir.IntType(32)))

    def __init__(self):
        pass

    @classmethod
    def convert_from(cls, func, typ, previous) -> ir.Instruction:
        if typ.name == "Range":
            return previous.eval(func)

    def convert_to(self, func, orig, typ) -> ir.Instruction:
        if typ.name == "Range":
            return orig.eval(func)

    def get_member_info(self, lhs, rhs):
        match rhs.var_name:
            case "start":
                return MemberInfo(False, False, Integer_32())
            case "end":
                return MemberInfo(False, False, Integer_32())
            case _:
                error("member not found!", line=rhs.position)

    def get_member(self, func, lhs,
                   rhs: "Ast.variable.VariableRef"):
        match rhs.var_name:
            case "start":
                start_ptr = func.builder.gep(lhs.get_ptr(func),
                                   [ir.Constant(ir.IntType(32), 0),
                                    ir.Constant(ir.IntType(32), 1)])
                return func.builder.load(start_ptr)
            case "end":
                end_ptr = func.builder.gep(lhs.get_ptr(func),
                                   [ir.Constant(ir.IntType(32), 0),
                                    ir.Constant(ir.IntType(32), 1)])
                return func.builder.load(end_ptr)
            case _:
                error("member not found!", line=rhs.position)

    def get_iter_return(self):
        return Integer_32()

    def iter_condition(self, func, self_ptr):
        end_ptr = func.builder.gep(self_ptr,
                                   [ir.Constant(ir.IntType(32), 0),
                                    ir.Constant(ir.IntType(32), 2)])
        end_val = func.builder.load(end_ptr)
        val_ptr = func.builder.gep(self_ptr,
                                   [ir.Constant(ir.IntType(32), 0),
                                    ir.Constant(ir.IntType(32), 1)])
        val_val = func.builder.load(val_ptr)
        return func.builder.icmp_signed("<", val_val, end_val)

    def iter(self, func, self_ptr):
        val_ptr = func.builder.gep(self_ptr,
                                   [ir.Constant(ir.IntType(32), 0),
                                    ir.Constant(ir.IntType(32), 2)])
        val_val = func.builder.load(val_ptr)
        addition = func.builder.add(val_val, ir.Constant(ir.IntType(32), 1))
        func.builder.store(addition, val_ptr)
        return addition

    def iter_get_val(self, func, self_ptr):
        val_ptr = func.builder.gep(self_ptr,
                                   [ir.Constant(ir.IntType(32), 0),
                                    ir.Constant(ir.IntType(32), 2)])
        val_val = func.builder.load(val_ptr)
        return val_val

