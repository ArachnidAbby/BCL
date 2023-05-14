from typing import Any

from llvmlite import ir

import Ast.Ast_Types.Type_Range
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition


class RangeLiteral(ExpressionNode):
    __slots__ = ('start', 'end')
    isconstant = False

    def __init__(self, pos: SrcPosition, start: Any, end: Any):
        super().__init__(pos)
        self.ret_type = Ast.Ast_Types.Type_Range.RangeType()
        self.start = start
        self.end = end
        self.ptr = None

    def pre_eval(self, func):
        self.start.pre_eval(func)
        self.end.pre_eval(func)

    def eval(self, func):
        self.start = self.start.eval(func)
        self.end = self.end.eval(func)
        ptr = self.get_ptr(func)
        self.put_at(func, ptr, 0, self.start)
        self.put_at(func, ptr, 1, self.end)
        self.put_at(func, ptr, 2, self.start)
        val = func.builder.load(ptr)
        return val

    def get_ptr(self, func):
        if self.ptr == None:
            self.ptr = func.create_const_var(self.ret_type)
        return self.ptr

    def put_at(self, func, ptr, idx, val):
        val_ptr = func.builder.gep(ptr, (ir.Constant(ir.IntType(64), 0), ir.Constant(ir.IntType(32), idx)))
        func.builder.store(val, val_ptr)

    def get_position(self) -> SrcPosition:
        return self.merge_pos((self.start.position, self.end.position))

    def repr_as_tree(self) -> str:
        return self.create_tree("Range Literal",
                                start=self.start,
                                end=self.end)
