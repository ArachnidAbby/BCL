from typing import Self

from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.math import MemberAccess
from Ast.nodes import KeyValuePair, ParenthBlock, Block
from Ast.nodes.passthrough import PassNode
from Ast.variables.reference import VariableRef
from Ast.nodes.commontypes import MemberInfo, Modifiers
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
                 'ir_type', 'module', 'visibility', 'can_create_literal', 'is_generic',
                 'versions', 'definition', 'needs_dispose', 'ref_counted')
    name = "STRUCT"
    pass_as_ptr = True
    no_load = False
    has_members = True

    # TODO: ADD __EQ__ CHECK FOR NAMESPACE
    def __init__(self, name: str, members: list[KeyValuePair], module,
                 is_generic, definition):
        self.struct_name = name
        self.raw_members = members
        self.members: dict[str, tuple[Ast_Types.Type, bool]] = {}  # bool "is_public"
        self.member_indexs = []
        self.member_index_search = {}
        self.returnable = True
        self.needs_dispose = False
        self.ref_counted = False
        self.can_create_literal = True
        self.versions = {}
        self.is_generic = is_generic
        self.definition = definition
        for c, member in enumerate(members):

            # populate member lists
            member_name = member.key.var_name
            self.member_indexs.append(member_name)
            self.member_index_search[member_name] = c

        if not self.is_generic:
            self.ir_type = ir.global_context.get_identified_type(f"{module.mod_name}.struct.{name}")
        else:
            self.ir_type = None
        self.size = len(self.member_indexs)-1
        self.module = module
        self.rang = None
        self.visibility = super().visibility

    def pass_type_params(self, func, params, pos):

        params_types = []

        for ty in params:
            params_types.append(ty.as_type_reference(func))

        params = tuple(params_types)

        if params in self.versions.keys():
            return self.versions[params]

        new_name = f"{self.struct_name}::<{', '.join([str(x) for x in params])}>"

        new_ty = Struct(new_name, self.raw_members, self.module,
                        False, self.definition)
        # new_ty.members = self.members

        for c, key in enumerate(self.definition.generic_args.keys()):
            self.definition.generic_args[key] = params[c]

        self.definition.struct_type = new_ty
        self.definition.is_generic = False

        self.versions[params] = new_ty

        self.definition.post_parse(self.module)
        self.definition.pre_eval(self.module)
        self.definition.eval(self.module)

        for c, key in enumerate(self.definition.generic_args.keys()):
            self.definition.generic_args[key] = None

        self.definition.struct_type = self
        self.definition.is_generic = True

        return new_ty

    def get_namespace_name(self, func, name, pos):
        if self.is_generic:
            error(f"Must pass type parameters\n hint: `{self}::<T>`",
                  line=pos)

        if x := self.global_namespace_names(func, name, pos):
            return x

        for mem_name in self.members.keys():
            if mem_name != name:
                continue
            val = self.members[mem_name][0]
            vis = self.members[mem_name][1]
            if not vis:
                error("Member is private", line=pos)

            if isinstance(val, Ast_Types.FunctionGroup) and not val.is_method:
                return val

        error(f"Name \"{name}\" cannot be " +
              f"found in Type \"{self.struct_name}\"",
              line=pos)

    def set_visibility(self, value):
        self.visibility = value

    def declare(self, mod):
        if self.is_generic:
            for ver in self.versions:
                self.versions[ver].declare(mod)
            return

        for name in self.members.keys():
            val = self.members[name][0]
            if isinstance(val, Ast_Types.FunctionGroup):
                val.declare(mod)

    def define(self, func):
        if self.is_generic:
            for ver in self.versions:
                self.versions[ver].define(func)
            return

        for member in self.raw_members:
            # when encountering an unreturnable type, make this struct
            # unreturnable
            if not member.get_type(func).returnable:
                self.returnable = False

            member_name = member.key.var_name

            if member.visibility == Modifiers.VISIBILITY_PRIVATE \
                    and self.visibility == Modifiers.VISIBILITY_PUBLIC:
                self.can_create_literal = False

            vis = member.visibility == Modifiers.VISIBILITY_PUBLIC
            typ = member.get_type(func)
            self.members[member_name] = (typ, vis)

            self.returnable = self.returnable and typ.returnable
            self.needs_dispose = self.needs_dispose or typ.needs_dispose
            self.ref_counted = self.ref_counted or typ.ref_counted

        self.ir_type.set_body(*[x[0].ir_type for x in self.members.values()])

    def create_function(self, name: str, func_typ):
        if name not in self.members.keys():
            self.members[name] = (Ast_Types.FunctionGroup(name, self.module), True)
        group = self.members[name][0]
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
        return super().__eq__(other) \
               and other.struct_name == self.struct_name \
               and self.module.location == other.module.location

    def __neq__(self, other):
        return super().__neq__(other) \
               and other.struct_name != self.struct_name \
               and self.module.location != other.module.location

    def get_func(self, name, lhs, rhs, ret_none=False):
        if rhs is not None:
            rhs_pos = rhs.position
        else:
            rhs_pos = (-1,-1,-1, "")
        args = ParenthBlock(rhs_pos)
        name_var = VariableRef(lhs.position, name, None)
        mem_access = MemberAccess(lhs.position, member_access_op, lhs, name_var)
        if rhs is not None:
            args.children = [rhs]
        args.in_func_call = True
        if name not in self.members.keys():
            if ret_none:
                return None
            error(f"No function \"{name}\" Found", line=lhs.position)
        return self.members[name][0].get_function(self, mem_access, args)

    def call_func(self, func, name, lhs, rhs):
        if rhs is not None:
            rhs_pos = rhs.position
        else:
            rhs_pos = (-1,-1,-1, "")
        args = ParenthBlock(rhs_pos)
        name_var = VariableRef(lhs.position, name, Block.BLOCK_STACK[-1])
        mem_access = MemberAccess(lhs.position, member_access_op, lhs, name_var)
        if rhs is not None:
            args.children = [rhs]
        args.in_func_call = True
        args.pre_eval(func)
        return self.members[name][0].call(func, mem_access, args)

    def get_op_return(self, func, op: str, lhs, rhs):
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
        typ = self.members[rhs.var_name][0]
        is_ptr = not isinstance(typ, Ast_Types.FunctionGroup)
        return MemberInfo(not typ.read_only, is_ptr, typ)

    def get_member(self, func, lhs,
                   member_name_in: "Ast.variable.VariableRef"):
        member_name = member_name_in.var_name
        if isinstance(self.members[member_name][0], Ast_Types.FunctionGroup):
            return self.members[member_name][0]
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

    def add_ref_count(self, func, ptr):
        int_type = ir.IntType(64)
        zero_const = ir.Constant(int_type, 0)
        tuple_ptr = ptr.get_ptr(func)

        func = self.get_func("__increase_ref_count__", ptr, None, ret_none=True)
        if func is not None:
            self.call_func(func, "__increase_ref_count__", ptr, None)

        for c, typ_tuple in enumerate(self.members.values()):
            typ = typ_tuple[0]
            if isinstance(typ, Ast_Types.FunctionGroup):
                continue
            if not typ.ref_counted:
                continue
            index = ir.Constant(int_type, c)
            p = func.builder.gep(tuple_ptr, [zero_const, index])
            node = PassNode(ptr.position, None, typ, ptr=p)
            typ.add_ref_count(func, node)

    def dispose(self, func, ptr):
        int_type = ir.IntType(64)
        zero_const = ir.Constant(int_type, 0)
        tuple_ptr = ptr.get_ptr(func)

        func = self.get_func("__dispose__", ptr, None, ret_none=True)
        if func is not None:
            self.call_func(func, "__dispose__", ptr, None)

        for c, typ_tuple in enumerate(self.members.values()):
            typ = typ_tuple[0]
            if isinstance(typ, Ast_Types.FunctionGroup):
                continue
            if not typ.needs_dispose:
                continue
            index = ir.Constant(int_type, c)
            p = func.builder.gep(tuple_ptr, [zero_const, index])
            node = PassNode(ptr.position, None, typ, ptr=p)
            typ.dispose(func, node)

    def __hash__(self):
        return hash(self.name+self.struct_name+self.module.mod_name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}--{self.struct_name}>'

    def __str__(self) -> str:
        return self.struct_name
