from typing import Self

from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.nodes import KeyValuePair
from Ast.nodes.commontypes import MemberInfo
from errors import error


class Struct(Ast_Types.Type):
    '''A class that defines the functionality of
    every struct type.
    '''

    __slots__ = ('struct_name', 'members', 'methods', 'member_indexs', 'size',
                 'rang', 'member_index_search', 'returnable', 'raw_members',
                 'ir_type')
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
        self.rang = None

    def define(self, func):
        for member in self.raw_members:
            # when encountering an unreturnable type, make this struct
            # unreturnable
            if not member.get_type(func).returnable:
                self.returnable = False

            member_name = member.key.var_name
            self.members[member_name] = member.get_type(func)
        self.ir_type.set_body(*[x.ir_type for x in self.members.values()])

    # TODO: allow casting overloads
    # "define __as__(&Self, x: othertype) -> Self;"
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

    # TODO: implement this
    def get_op_return(self, op, lhs, rhs):
        pass

    def get_member_info(self, lhs, rhs):
        if rhs.var_name not in self.members.keys():
            error("member not found!", line=rhs.position)
        return MemberInfo(True, True, self.members[rhs.var_name])

    def get_member(self, func, lhs,
                   member_name_in: "Ast.variable.VariableRef"):
        member_name = member_name_in.var_name
        member_index = self.member_index_search[member_name]
        # ^ no need to check if it exists.
        # We do this when getting the return type
        zero_const = ir.Constant(ir.IntType(64), 0)
        idx = ir.Constant(ir.IntType(32), member_index)
        return func.builder.gep(lhs.get_ptr(func), [zero_const, idx])

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
