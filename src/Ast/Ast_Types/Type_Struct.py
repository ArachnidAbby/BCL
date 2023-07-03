from typing import Self

from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.math import MemberAccess
from Ast.nodes import KeyValuePair, ParenthBlock
from Ast.variables.reference import VariableRef
from Ast.nodes.commontypes import MemberInfo
from Ast.reference import Ref
from errors import error
import Ast.math

member_access_op = Ast.math.ops["access_member"]

struct_op_overloads = {
    "sum": "__add__",
    "sub": "__sub__",
    "mul": "__mul__",
    "div": "__div__",
    "mod": "__mod__",
    "eq": "__eq__",
    "ne": "__ne__",
    "le": "__lt__",
    "gr": "__gt__",
    "geq": "__geq__",
    "leq": "__leq__",
    "imul": "__imul__",
    "idiv": "__idiv__",
    "isub": "__isub__",
    "isum": "__iadd__"
}


class Struct(Ast_Types.Type):
    '''A class that defines the functionality of
    every struct type.
    '''

    __slots__ = ('struct_name', 'members', 'methods', 'member_indexs', 'size',
                 'rang', 'member_index_search', 'returnable', 'raw_members',
                 'ir_type', 'module')
    name = "STRUCT"
    pass_as_ptr = True
    no_load = False
    has_members = True

    # TODO: implement struct methods
    def __init__(self, name: str, members: list[KeyValuePair], module):
        self.struct_name = name
        self.raw_members = members
        self.members: dict[str, Ast_Types.Type] = {}
        self.member_indexs = []
        self.member_index_search = {}
        self.returnable = True
        for c, member in enumerate(members):

            # populate member lists
            member_name = member.key.var_name
            self.member_indexs.append(member_name)
            self.member_index_search[member_name] = c

        self.ir_type = ir.global_context.get_identified_type(f"struct.{name}")
        self.size = len(self.member_indexs)-1
        self.module = module
        self.rang = None

    def declare(self, mod):
        for name in self.members.keys():
            val = self.members[name]
            if isinstance(val, Ast_Types.FunctionGroup):
                val.declare(mod)

    def define(self, func):
        for member in self.raw_members:
            # when encountering an unreturnable type, make this struct
            # unreturnable
            if not member.get_type(func).returnable:
                self.returnable = False

            member_name = member.key.var_name
            self.members[member_name] = member.get_type(func)
        self.ir_type.set_body(*[x.ir_type for x in self.members.values()])

    def create_function(self, name: str, func_typ):
        if name not in self.members.keys():
            self.members[name] = Ast_Types.FunctionGroup(name, self.module)
        group = self.members[name]
        group.add_function(func_typ)  # type: ignore
        return group

    # TODO: allow casting overloads
    # "define __as__::<other_type>(&Self) -> other_type;"
    @classmethod
    def convert_from(cls, func, typ, previous) -> ir.Instruction:
        if typ == previous.ret_type:
            return typ
        error("Struct type has no conversions",  line=previous.position)

    def convert_to(self, func, orig, typ) -> ir.Instruction:
        if typ == orig.ret_type:
            return orig.eval(func)
        error(f"{self.struct_name} has no conversions",  line=orig.position)

    def __eq__(self, other):
        return super().__eq__(other) and other.struct_name == self.struct_name

    def __neq__(self, other):
        return super().__neq__(other) and other.struct_name != self.struct_name

    def get_func(self, name, lhs, rhs):
        args = ParenthBlock(rhs.position)
        name_var = VariableRef(lhs.position, name, None)
        mem_access = MemberAccess(lhs.position, member_access_op, lhs, name_var)
        args.children = [rhs]
        args.in_func_call = True
        if name not in self.members.keys():
            error(f"No function \"{name}\" Found", line=lhs.position)
        return self.members[name].get_function(mem_access, args)

    def call_func(self, func, name, lhs, rhs):
        args = ParenthBlock(rhs.position)
        name_var = VariableRef(lhs.position, name, None)
        mem_access = MemberAccess(lhs.position, member_access_op, lhs, name_var)
        mem_access.pre_eval(func)
        args.children = [rhs]
        args.in_func_call = True
        args.pre_eval(func)
        mem_access.pre_eval(func)
        return self.members[name].call(func, mem_access, args)

    def get_op_return(self, op: str, lhs, rhs):
        op_name = struct_op_overloads.get(op.lower())
        self._simple_call_op_error_check(op, lhs, rhs)
        if op_name is None:
            return
        return self.get_func(op_name, lhs, rhs).func_ret

    def sum(self, func, lhs, rhs):
        return self.call_func(func, "__add__", lhs, rhs)

    def sub(self, func, lhs, rhs):
        return self.call_func(func, "__sub__", lhs, rhs)

    def mul(self, func, lhs, rhs):
        return self.call_func(func, "__mul__", lhs, rhs)

    def div(self, func, lhs, rhs):
        return self.call_func(func, "__div__", lhs, rhs)

    def eq(self, func, lhs, rhs):
        return self.call_func(func, "__eq__", lhs, rhs)

    def neq(self, func, lhs, rhs):
        return self.call_func(func, "__neq__", lhs, rhs)

    def le(self, func, lhs, rhs):
        return self.call_func(func, "__lt__", lhs, rhs)

    def gr(self, func, lhs, rhs):
        return self.call_func(func, "__gt__", lhs, rhs)

    def leq(self, func, lhs, rhs):
        return self.call_func(func, "__leq__", lhs, rhs)

    def geq(self, func, lhs, rhs):
        return self.call_func(func, "__geq__", lhs, rhs)

    def isum(self, func, lhs, rhs):
        return self.call_func(func, "__iadd__", Ref(lhs.position, lhs), rhs)

    def isub(self, func, lhs, rhs):
        return self.call_func(func, "__isub__", Ref(lhs.position, lhs), rhs)

    def imul(self, func, lhs, rhs):
        return self.call_func(func, "__imul__", Ref(lhs.position, lhs), rhs)

    def idiv(self, func, lhs, rhs):
        return self.call_func(func, "__idiv__", Ref(lhs.position, lhs), rhs)

    def get_member_info(self, lhs, rhs):
        if rhs.var_name not in self.members.keys():
            error("member not found!", line=rhs.position)
        typ = self.members[rhs.var_name]
        is_ptr = not isinstance(typ, Ast_Types.FunctionGroup)
        return MemberInfo(not typ.read_only, is_ptr, typ)

    def get_member(self, func, lhs,
                   member_name_in: "Ast.variable.VariableRef"):
        member_name = member_name_in.var_name
        if isinstance(self.members[member_name], Ast_Types.FunctionGroup):
            return self.members[member_name]
        member_index = self.member_index_search[member_name]
        # ^ no need to check if it exists.
        # We do this when getting the return type
        zero_const = ir.Constant(ir.IntType(64), 0)
        idx = ir.Constant(ir.IntType(32), member_index)
        return func.builder.gep(lhs.get_ptr(func), [zero_const, idx])

    # TODO:
    def index(self, func, lhs) -> ir.Instruction:
        return func.builder.load(lhs.get_ptr(func))

    def put(self, func, lhs, value):
        error(f"Operation 'put-at' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def __hash__(self):
        return hash(self.name+self.struct_name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}--{self.struct_name}>'

    def __str__(self) -> str:
        return self.struct_name
