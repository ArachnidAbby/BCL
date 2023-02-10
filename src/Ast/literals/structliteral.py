from llvmlite import ir

import errors
from Ast.nodes import Block, ExpressionNode, KeyValuePair
from Ast.nodes.commontypes import SrcPosition


class StructLiteral(ExpressionNode):
    __slots__ = ('members',)
    isconstant = False

    def __init__(self, pos: SrcPosition, name, members: Block):
        super().__init__(pos)
        self.members = members
        self.ret_type = name.as_type_reference()

    def pre_eval(self, func):
        self.members.pre_eval(func)
        for child in self.members:
            if not isinstance(child, KeyValuePair):
                errors.error("Invalid Syntax:", line=child.position)
            child.value.pre_eval(func)

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

    @property
    def position(self) -> SrcPosition:
        return self.merge_pos((self._position,
                               *[x.position for x in self.members.children]))
