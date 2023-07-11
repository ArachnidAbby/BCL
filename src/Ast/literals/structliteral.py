from llvmlite import ir
from Ast.Ast_Types import Type_Function# type: ignore

import errors
from Ast.nodes import Block, ExpressionNode, KeyValuePair
from Ast.nodes.commontypes import SrcPosition
from Ast.Ast_Types.Type_Struct import Struct


class StructLiteral(ExpressionNode):
    __slots__ = ('members', 'struct_name')
    isconstant = False

    def __init__(self, pos: SrcPosition, name, members: Block):
        super().__init__(pos)
        self.members = members
        self.struct_name = name

    def pre_eval(self, func):
        self.ret_type = self.struct_name.as_type_reference(func)
        if not isinstance(self.ret_type, Struct):
            errors.error("Type is not a structure",
                         line=self.position)

        if not self.ret_type.can_create_literal and func.module.location != self.ret_type.module.location:
            errors.error("Type has private members, cannot " +
                         "create a struct literal from this type",
                         line=self.position)

        used_names = []
        missing_members = []

        # self.members.pre_eval(func)
        for child in self.members:
            if not isinstance(child, KeyValuePair):
                errors.error("Invalid Syntax:", line=child.position)
            child.value.pre_eval(func)
            name = child.key.var_name
            used_names.append(name)
            if name not in self.ret_type.members.keys():
                errors.error(f"{self.ret_type} has no member " +
                             f"\"{child.key.var_name}\"",
                             line=child.key.position)
            if child.value.ret_type != self.ret_type.members[name][0]:
                errors.error(f"Expected type {self.ret_type.members[name]} " +
                             f"got {child.value.ret_type}",
                             line=child.value.position)

        for x in self.ret_type.members.keys():
            ty = self.ret_type.members[x][0]
            if isinstance(ty, Type_Function.Function) or isinstance(ty, Type_Function.FunctionGroup):
                continue
            if x not in used_names:
                missing_members.append(x)

        if len(missing_members) > 0:
            missing_str = ", ".join([f"\"{x}\"" for x in missing_members])
            errors.error(f"Missing required members: {missing_str} ",
                         line=self.position)

    def eval_impl(self, func):
        ptr = func.create_const_var(self.ret_type)
        zero_const = ir.Constant(ir.IntType(64), 0)
        idx_lookup = {name: idx for idx, name in
                      enumerate(self.ret_type.member_indexs)}
        for child in self.members:
            index = ir.Constant(ir.IntType(32), idx_lookup[child.key.var_name])
            item_ptr = func.builder.gep(ptr, [zero_const, index])
            value = child.value.eval_impl(func)
            child.value._instruction = value
            func.builder.store(value, item_ptr)
        self.ptr = ptr
        self._instruction = func.builder.load(ptr)
        return self._instruction

    def get_position(self) -> SrcPosition:
        return self.merge_pos((self._position,
                               *[x.position for x in self.members.children]))

    def repr_as_tree(self) -> str:
        return self.create_tree("Struct Literal",
                                members=self.members,
                                struct_name=self.struct_name)
