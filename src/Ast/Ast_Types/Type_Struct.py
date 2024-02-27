from typing import Any

from llvmlite import ir

import Ast.math
from Ast import Ast_Types
from Ast.Ast_Types.Type_Alias import Alias  # type: ignore
from Ast.Ast_Types.Type_Base import struct_op_overloads
from Ast.Ast_Types.Type_Bool import Integer_1
from Ast.Ast_Types.Type_Function import FunctionGroup
from Ast.Ast_Types.Type_Void import Void
from Ast.math import MemberAccess
from Ast.nodes import Block, KeyValuePair, ParenthBlock
from Ast.nodes.block import create_const_var
from Ast.nodes.commontypes import Lifetimes, MemberInfo, Modifiers, SrcPosition
from Ast.nodes.container import ContainerNode
from Ast.nodes.passthrough import PassNode
from Ast.reference import Ref
from Ast.variables.reference import VariableRef
from errors import error

member_access_op = Ast.math.ops["access_member"]


# TODO: FINISH THIS DAMN THING!
class QualifiedStruct(Ast_Types.Type):
    __slots__ = ("struct_type", "member_lifetimes")

    def __init__(self, struct_type):
        self.struct_type = struct_type
        self.member_lifetimes: dict[str, Lifetimes] = {}

    def get_member_info(self, lhs, rhs, avoid_recursion=False):
        # if len(self.member_lifetimes) == 0:
        #     for name in self.struct_type.members.keys():
        #         self.member_lifetimes[name] = Lifetimes.UNKNOWN

        member_info = self.struct_type.get_member_info(lhs, rhs,
                                                       avoid_recursion=avoid_recursion)

        # member_info.lifetime = self.member_lifetimes[rhs.var_name]
        return member_info

    def __getattribute__(self, attr_name: str) -> Any:
        if attr_name in ("member_lifetimes", "get_member_info", "struct_type"):
            return object.__getattribute__(self, attr_name)
        return object.__getattribute__(self.struct_type, attr_name)


class Struct(Ast_Types.Type):
    '''A class that defines the functionality of
    every struct type.
    '''

    __slots__ = ('struct_name', 'members', 'methods', 'member_indexs', 'size',
                 'rang', 'member_index_search', 'returnable', 'raw_members',
                 'ir_type', 'module', 'visibility', 'can_create_literal',
                 'is_generic', 'versions', 'definition', 'needs_dispose',
                 'ref_counted', 'is_wrapper')
    name = "STRUCT"
    pass_as_ptr = True
    no_load = False
    has_members = True
    index_returns_ptr = False

    # TODO: ADD __EQ__ CHECK FOR NAMESPACE
    def __init__(self, name: str, members: list[KeyValuePair], module,
                 is_generic, definition):
        self.struct_name = name
        self.raw_members = members
        # bool "is_public"
        self.members: dict[str, tuple[Ast_Types.Type, bool]] = {}
        self.member_indexs = []
        self.member_index_search = {}
        self.returnable = True
        self.is_wrapper = False
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

        self.ir_type: ir.Type | None = None
        if not self.is_generic:
            name = f"{module.mod_name}.struct.{name}"
            self.ir_type = ir.global_context.get_identified_type(name)

        self.size = len(self.member_indexs)-1
        self.module = module
        self.rang = None
        self.visibility = super().visibility

    def __call__(self):
        return QualifiedStruct(self)

    def pass_type_params(self, func, params, pos):

        params_types = []

        for ty in params:
            params_types.append(ty.as_type_reference(func))

        params = tuple(params_types)

        if len(params) != len(self.definition.generic_args):
            error("Invalid Generic arguments. Not enough args",
                  line=pos)

        if Void() in params:
            return self

        if params in self.versions.keys():
            return self.versions[params][0]

        str_params = ', '.join([x.__str__() for x in params])
        new_name = f"{self.struct_name}::<{str_params}>"

        generic_args = {**self.definition.generic_args}

        for c, key in enumerate(self.definition.generic_args.keys()):
            generic_args[key] = (params[c], func)

        def_copy = self.definition.copy()
        def_copy.is_generic = False
        def_copy.struct_name = new_name
        def_copy.generic_args = generic_args
        members = []
        if isinstance(def_copy.block.children[0], ContainerNode):
            members = def_copy.block.children[0].children
        elif isinstance(def_copy.block.children[0], KeyValuePair):
            members = [def_copy.block.children[0]]
        new_ty = Struct(new_name, members, self.module,
                        False, def_copy)
        new_ty.is_wrapper = self.is_wrapper
        def_copy.struct_type = new_ty

        self.versions[params] = (new_ty, generic_args, def_copy, pos)

        self.definition.fullfill_templates(self.module)

        return new_ty

    def get_namespace_name(self, func, name, pos):
        from Ast.module import NamespaceInfo
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
                return NamespaceInfo(val, {})

        error(f"Name \"{name}\" cannot be " +
              f"found in Type \"{self.struct_name}\"",
              line=pos)

    def set_visibility(self, value):
        self.visibility = value

    def declare(self, mod):
        if self.is_generic:
            for ver in self.versions:
                self.versions[ver][0].declare(mod)
            return

        for name in self.members.keys():
            val = self.members[name][0]
            if isinstance(val, Ast_Types.FunctionGroup):
                val.declare(mod)

    def define(self, func):
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
        if isinstance(other, Alias):
            return self.name == other.dealias().name \
               and other.dealias().struct_name == self.struct_name \
               and self.module.location == other.dealias().module.location

        return super().__eq__(other) \
            and other.struct_name == self.struct_name \
            and self.module.location == other.module.location

    def __neq__(self, other):
        if isinstance(other.ret_type, Alias):
            return self.name != other.dealias().name \
               or other.struct_name != self.struct_name \
               or self.module.location != other.module.location

        return super().__neq__(other) \
               or other.struct_name != self.struct_name \
               or self.module.location != other.module.location

    def get_func(self, func, name, lhs, rhs, ret_none=False):
        if rhs is not None:
            rhs_pos = rhs.position
        else:
            rhs_pos = SrcPosition.invalid()
        args = ParenthBlock(rhs_pos)
        name_var = VariableRef(lhs.position, name, None)
        mem_access = MemberAccess(lhs.position, member_access_op, lhs, name_var)
        if rhs is not None:
            args.children = [rhs]
        args.in_func_call = True
        if self.get_member_info(lhs, name_var) is None:
            if ret_none:
                return None
            error(f"No function \"{name}\" Found", line=lhs.position)
        fetched_func = self.get_member_info(lhs, name_var).typ

        if name not in self.members.keys():
            unwrap_func = self._get_unwrap_function(lhs, rhs)
            if unwrap_func is None:
                return None

            unwrap_node = PassNode(lhs.position, None,
                                   unwrap_func.func_ret)

            args.children[0] = unwrap_node

        if isinstance(fetched_func, FunctionGroup):
            return fetched_func.get_function(self, mem_access, args)
        else:
            return fetched_func

    def get_func_scoped(self, func, name, lhs, rhs, ret_none=False):
        '''Limit search to this specific type, ignore wrapping'''
        if rhs is not None:
            rhs_pos = rhs.position
        else:
            rhs_pos = SrcPosition.invalid()
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
            rhs_pos = SrcPosition.invalid()
        args = ParenthBlock(rhs_pos)
        name_var = VariableRef(lhs.position, name, Block.BLOCK_STACK[-1])
        mem_access = MemberAccess(lhs.position, member_access_op, lhs, name_var)
        if rhs is not None:
            args.children = [rhs]
        args.in_func_call = True
        if name not in self.members:
            unwrap_res = self.call_func(func, "__unwrap__", lhs, None)
            unwrap_func = self._get_unwrap_function(lhs, rhs)
            if unwrap_func is None:
                return None

            unwrap_node = PassNode(lhs.position, unwrap_res,
                                   unwrap_func.func_ret)

            args.children[0] = unwrap_node
        args.pre_eval(func)

        return self.get_member(func, lhs, name_var).call(func, mem_access, args)

    def get_op_return(self, func, op: str, lhs, rhs):
        op_name = struct_op_overloads.get(op.lower())
        # self._simple_call_op_error_check(op, lhs, rhs)
        if op_name is None:
            return
        if op_name == "__bitnot__":
            return self.get_func(func, op_name, lhs, None).func_ret
        if op_name == "__call__":
            args = ParenthBlock(rhs.position)
            name_var = VariableRef(lhs.position, "__call__", None)
            mem_access = MemberAccess(lhs.position, member_access_op, lhs, name_var)
            if isinstance(rhs, ParenthBlock):
                args.children = rhs.children
            else:
                args.children = [rhs]
            args.in_func_call = True
            if "__call__" not in self.members.keys():
                error("No function \"__call__\" Found", line=lhs.position)
            return self.members["__call__"][0].get_function(func, mem_access, args).func_ret
        return self.get_func(func, op_name, lhs, rhs).func_ret

    def sum(self, func, lhs, rhs):
        return self.call_func(func, "__add__", lhs, rhs)

    def sub(self, func, lhs, rhs):
        return self.call_func(func, "__sub__", lhs, rhs)

    def mul(self, func, lhs, rhs):
        return self.call_func(func, "__mul__", lhs, rhs)

    def div(self, func, lhs, rhs):
        return self.call_func(func, "__div__", lhs, rhs)

    def pow(self, func, lhs, rhs):
        return self.call_func(func, "__pow__", lhs, rhs)

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

    def lshift(self, func, lhs, rhs) -> ir.Instruction:
        return self.call_func(func, "__lshift__", lhs, rhs)

    def rshift(self, func, lhs, rhs) -> ir.Instruction:
        return self.call_func(func, "__rshift__", lhs, rhs)

    def bit_not(self, func, lhs) -> ir.Instruction:
        return self.call_func(func, "__bitnot__", lhs, None)

    def bit_xor(self, func, lhs, rhs) -> ir.Instruction:
        return self.call_func(func, "__bitxor__", lhs, rhs)

    def bit_or(self, func, lhs, rhs) -> ir.Instruction:
        return self.call_func(func, "__bitor__", lhs, rhs)

    def bit_and(self, func, lhs, rhs) -> ir.Instruction:
        return self.call_func(func, "__bitand__", lhs, rhs)

    def _get_unwrap_function(self, lhs, rhs, mut=False):
        if not self.is_wrapper:
            return None
        if mut:
            func_name = "__unwrap_mut__"
        else:
            func_name = "__unwrap__"
        return self.get_func_scoped(None, func_name, lhs, None, True)

    def _get_wrapped_member_info(self, lhs, rhs):
        unwrap_func = self._get_unwrap_function(lhs, rhs)
        if unwrap_func is None:
            return None

        typ = unwrap_func.func_ret
        unwrap_node = PassNode(lhs.position, None, typ)
        if isinstance(typ, QualifiedStruct) or isinstance(typ, Struct):
            return typ.get_member_info(unwrap_node, rhs, avoid_recursion=True)
        else:
            return typ.get_member_info(unwrap_node, rhs)

    # def _get_wrapped_member(self, func, lhs, rhs):
    #     unwrap_func = self._get_unwrap_function(lhs, rhs)
    #     if unwrap_func is None:
    #         return None

    #     typ = unwrap_func.func_ret
    #     unwrap_node = PassNode(lhs.position, None, typ)
    #     return typ.get_member(func, lhs, rhs)

    def get_member_info(self, lhs, rhs, avoid_recursion=False):
        if rhs.var_name not in self.members.keys() and not avoid_recursion:
            info = self._get_wrapped_member_info(lhs, rhs)
            if info is not None:
                info.causes_unwrap = True
            return info
        elif rhs.var_name not in self.members.keys():
            return None
        typ = self.members[rhs.var_name][0]
        is_ptr = not isinstance(typ, Ast_Types.FunctionGroup)
        return MemberInfo(not typ.read_only, is_ptr, typ)

    def unwrap(self, func, lhs) -> tuple[PassNode, "Function"]:
        unwrap_res = self.call_func(func, "__unwrap__", lhs, None)
        unwrap_func = self._get_unwrap_function(lhs, None)
        if unwrap_func is None:
            return None

        return PassNode(lhs.position, unwrap_res,
                        unwrap_func.func_ret), unwrap_func

    def unwrap_mut(self, func, lhs) -> tuple[PassNode, "Function"]:
        unwrap_res = self.call_func(func, "__unwrap_mut__", lhs, None)
        unwrap_func = self._get_unwrap_function(lhs, None, mut=True)
        if unwrap_func is None:
            return None

        return PassNode(lhs.position, None,
                        unwrap_func.func_ret, unwrap_res), unwrap_func

    def get_member(self, func, lhs,
                   member_name_in: "Ast.variable.VariableRef"):
        member_name = member_name_in.var_name

        if member_name not in self.members.keys():
            unwrap_node, unwrap_func = self.unwrap(func, lhs)

            return unwrap_func.func_ret.get_member(func, unwrap_node,
                                                   member_name_in)

        if isinstance(self.members[member_name][0], Ast_Types.FunctionGroup):
            return self.members[member_name][0]
        member_index = self.member_index_search[member_name]
        # ^ no need to check if it exists.
        # We do this when getting the return type
        zero_const = ir.Constant(ir.IntType(64), 0)
        idx = ir.Constant(ir.IntType(32), member_index)
        return func.builder.gep(lhs.get_ptr(func), [zero_const, idx])

    # # TODO:
    # def index(self, func, var, ind) -> ir.Instruction:
    #     return self.call_func(func, "__index__", var.position, var, ind)

    # def put(self, func, lhs, value):
    #     return self.call_func(func, "__put_at__", Ref(lhs.position, lhs), value)

    def get_iter_return(self, func, node):
        function = self.get_func(func, "__iter__", node, None)
        return function.func_ret

    def create_iterator(self, func, val, loc):
        actual_value = self.call_func(func, "__iter__", val, None)
        var = create_const_var(func, self.get_iter_return(func, val))
        func.builder.store(actual_value, var)

        return var

    def deref(self, func, node):
        return self.call_func(func, "__deref__", node, None)

    def truthy(self, func, lhs):
        function = self.get_func(func, "__truthy__", lhs, None)
        if function.func_ret != Integer_1():
            error("\"__truthy__\" must return a boolean",
                  line=func.definition.position)
        return self.call_func(func, "__truthy__", lhs, None)

    def get_deref_return(self, func, node):
        function = self.get_func(func, "__deref__", node, None)
        return function.func_ret

    def call(self, func, lhs, args) -> ir.Instruction:
        real_args = ParenthBlock(args.position)
        name_var = VariableRef(lhs.position, "__call__", None)
        mem_access = MemberAccess(lhs.position, member_access_op, lhs, name_var)
        if isinstance(args, ParenthBlock):
            real_args.children = args.children
        else:
            real_args.children = [args]
        real_args.in_func_call = True
        if "__call__" not in self.members.keys():
            error("No function \"__call__\" Found", line=lhs.position)
        return self.members["__call__"][0].call(func, mem_access, real_args)

    def add_ref_count(self, func, ptr):
        if func.func_name in ("__increase_ref_count__", "__dispose__") and func.parent is self.definition:
            return

        int_type = ir.IntType(64)
        int32_type = ir.IntType(32)
        zero_const = ir.Constant(int_type, 0)
        struct_ptr = ptr.get_ptr(func)

        function = self.get_func(func, "__increase_ref_count__", ptr, None, ret_none=True)
        if function is not None:
            self.call_func(func, "__increase_ref_count__", ptr, None)

        for c, typ_tuple in enumerate(self.members.values()):
            typ = typ_tuple[0]
            if isinstance(typ, Ast_Types.FunctionGroup):
                continue
            if not typ.ref_counted:
                continue
            index = ir.Constant(int32_type, c)
            p = func.builder.gep(struct_ptr, [zero_const, index])
            node = PassNode(ptr.position, None, typ, ptr=p)
            typ.add_ref_count(func, node)

    def dispose(self, func, ptr):
        if func.func_name in ("__increase_ref_count__", "__dispose__") and func.parent is self.definition:
            return
        int_type = ir.IntType(64)
        int32_type = ir.IntType(32)

        zero_const = ir.Constant(int_type, 0)
        struct_ptr = ptr.get_ptr(func)

        function = self.get_func(func, "__dispose__", ptr, None, ret_none=True)
        if function is not None:
            self.call_func(func, "__dispose__", ptr, None)

        for c, typ_tuple in enumerate(self.members.values()):
            typ = typ_tuple[0]
            if isinstance(typ, Ast_Types.FunctionGroup):
                continue
            if not typ.needs_dispose:
                continue
            index = ir.Constant(int32_type, c)
            p = func.builder.gep(struct_ptr, [zero_const, index])
            node = PassNode(ptr.position, None, typ, ptr=p)
            typ.dispose(func, node)

    def __hash__(self):
        return hash(self.name+self.struct_name+self.module.mod_name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}--{self.struct_name}>'

    def __str__(self) -> str:
        return self.struct_name
