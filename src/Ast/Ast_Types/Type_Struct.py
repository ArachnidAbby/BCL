from typing import Self

from llvmlite import ir

from Ast import Ast_Types
from Ast.nodes import KeyValuePair
from errors import error


class Struct(Ast_Types.Type):
    '''abstract type class that outlines the necessary features of a type class.'''

    __slots__ = ('struct_name', 'members', 'methods', 'member_indexs', 'size',
                 'rang', 'member_index_search', 'returnable', 'raw_members')
    name = "STRUCT"
    pass_as_ptr = True
    no_load = False
    has_members = True

    # TODO: implement struct methods
    def __init__(self, name: str, members: list[KeyValuePair], module):
        self.struct_name = name
        self.raw_members = members
        self.members = {}
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
            # when encountering an unreturnable type, make this struct unreturnable
            if not member.get_type(func).returnable:
                self.returnable = False

            member_name = member.key.var_name
            self.members[member_name] = member.get_type(func)
        self.ir_type.set_body(*[x.ir_type for x in self.members.values()])

    # TODO: allow casting overloads
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
        if op == "access_member":
            if rhs.var_name not in self.members.keys():
                error("member not found!", line=rhs.position)
            return self.members[rhs.var_name]

    def get_member(self, func, lhs, member_name_in: "Ast.variable.VariableRef"):
        member_name = member_name_in.var_name
        member_index = self.member_index_search[member_name]
        # ^ no need to check if it exists.
        # We do this when getting the return type
        zero_const = ir.Constant(ir.IntType(64), 0)
        idx = ir.Constant(ir.IntType(32), member_index)
        return func.builder.gep(lhs.get_ptr(func), [zero_const, idx])

    # def sum  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '+' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def sub  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '-' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def mul  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '*' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def div  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '/' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def mod  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '%' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def pow (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '**' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def eq   (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '==' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def neq  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '!=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def geq  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '>=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def leq  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def le   (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def gr   (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def _not (self, func, rhs) -> ir.Instruction: error(f"Operator 'not' is not supported for type '{rhs.ret_type}'", line = rhs.position)

    # def _and (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator 'and' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    # def _or  (self, func, lhs, rhs) -> ir.Instruction: error(f"Operator 'or' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    def index(self, func, lhs) -> ir.Instruction:
        return func.builder.load(lhs.get_ptr(func))

    def put(self, func, lhs, value):
        error(f"Operation 'putat' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    # def assign(self, func, ptr, value, typ: Self):
    #     val = value.ret_type.convert_to(func, value, typ)  # type: ignore
    #     func.builder.store(val, ptr.ptr)

    # def isum(self, func, ptr, rhs):
    #     final_value = self.sum(func, ptr, rhs)
    #     ptr = ptr.get_ptr(func)
    #     func.builder.store(final_value, ptr)

    # def isub(self, func, ptr, rhs):
    #     final_value = self.sub(func, ptr, rhs)
    #     ptr = ptr.get_ptr(func)
    #     func.builder.store(final_value, ptr)

    # def imul(self, func, ptr, rhs):
    #     final_value = self.mul(func, ptr, rhs)
    #     ptr = ptr.get_ptr(func)
    #     func.builder.store(final_value, ptr)


    # def idiv(self, func, ptr, rhs):
    #     final_value = self.div(func, ptr, rhs)
    #     ptr = ptr.get_ptr(func)
    #     func.builder.store(final_value, ptr)

    def __hash__(self):
        return hash(self.name+self.struct_name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}--{self.struct_name}>'

    def __str__(self) -> str:
        return self.struct_name

    def __call__(self) -> Self:
        return self
