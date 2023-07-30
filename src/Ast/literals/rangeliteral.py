from typing import Any

from llvmlite import ir

import Ast.Ast_Types.Type_Range
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition
import errors


class RangeLiteral(ExpressionNode):
    __slots__ = ('start', 'end')
    isconstant = False

    def __init__(self, pos: SrcPosition, start: Any, end: Any):
        super().__init__(pos)
        self.ret_type = Ast.Ast_Types.Type_Range.RangeType()
        self.start = start
        self.end = end
        self.ptr = None

    def copy(self):
        out = RangeLiteral(self._position, self.start.copy(), self.end.copy())

    def fullfill_templates(self, func):
        self.start.fullfill_templates(func)
        self.end.fullfill_templates(func)

    def post_parse(self, func):
        self.start.post_parse(func)
        self.end.post_parse(func)

    def pre_eval(self, func):
        self.start.pre_eval(func)
        self.end.pre_eval(func)

        if self.start.ret_type.name != "i32":
            errors.error("Start of range literal must be an i32",
                         self.start.position)

        if self.end.ret_type.name != "i32":
            errors.error("End of range literal must be an i32",
                         self.end.position)

    def eval_impl(self, func):
        start = self.start.eval_impl(func)
        self.start._instruction = start
        end = self.end.eval_impl(func)
        self.end._instruction = end
        ptr = self.get_ptr(func)
        self._put_at(func, ptr, 0, start)
        self._put_at(func, ptr, 1, end)
        self._put_at(func, ptr, 2, start)
        val = func.builder.load(ptr)
        return val

    def get_ptr(self, func):
        if self.ptr is None:
            self.ptr = func.create_const_var(self.ret_type)
        return self.ptr

    def _put_at(self, func, ptr, idx, val):
        val_ptr = func.builder.gep(ptr, (ir.Constant(ir.IntType(64), 0),
                                         ir.Constant(ir.IntType(32), idx)))
        func.builder.store(val, val_ptr)

    def get_position(self) -> SrcPosition:
        return self.merge_pos((self.start.position, self.end.position))

    def repr_as_tree(self) -> str:
        return self.create_tree("Range Literal",
                                start=self.start,
                                end=self.end)
