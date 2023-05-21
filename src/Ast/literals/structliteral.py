from llvmlite import ir  # type: ignore

import errors
from Ast.nodes import Block, ExpressionNode, KeyValuePair
from Ast.nodes.commontypes import SrcPosition


class StructLiteral(ExpressionNode):
    __slots__ = ('members', 'struct_name')
    isconstant = False

    def __init__(self, pos: SrcPosition, name, members: Block):
        super().__init__(pos)
        self.members = members
        self.struct_name = name

    def pre_eval(self, func):
        self.ret_type = self.struct_name.as_type_reference(func)
        # self.members.pre_eval(func)
        for child in self.members:
            if not isinstance(child, KeyValuePair):
                errors.error("Invalid Syntax:", line=child.position)
            child.value.pre_eval(func)
            name = child.key.var_name
            if child.value.ret_type != self.ret_type.members[name]:
                errors.error(f"Expected type {self.ret_type.members[name]} " +
                             f"got {child.value.ret_type}",
                             line=child.value.position)

    def eval(self, func):
        ptr = func.create_const_var(self.ret_type)
        zero_const = ir.Constant(ir.IntType(64), 0)
        idx_lookup = {name: idx for idx, name in
                      enumerate(self.ret_type.member_indexs)}
        for child in self.members:
            index = ir.Constant(ir.IntType(32), idx_lookup[child.key.var_name])
            item_ptr = func.builder.gep(ptr, [zero_const, index])
            func.builder.store(child.value.eval(func), item_ptr)
        self.ptr = ptr
        return func.builder.load(ptr)

    def get_position(self) -> SrcPosition:
        return self.merge_pos((self._position,
                               *[x.position for x in self.members.children]))

    def repr_as_tree(self) -> str:
        return self.create_tree("Struct Literal",
                                members=self.members,
                                struct_name=self.struct_name)
