from typing import Any

from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition


class RangeLiteral(ExpressionNode):
    __slots__ = ('start', 'end')
    isconstant = True

    def __init__(self, pos: SrcPosition, start: Any, end: Any):
        super().__init__(pos)
        self.start = start
        self.end = end

    def pre_eval(self, func):
        self.start.pre_eval(func)
        self.end.pre_eval(func)

    def eval(self, func):
        self.start = self.start.eval(func)
        self.end = self.end.eval(func)

    def get_position(self) -> SrcPosition:
        return self.merge_pos((self.start.position, self.end.position))

    def repr_as_tree(self) -> str:
        return self.create_tree("Range Literal",
                                start=self.start,
                                end=self.end)
