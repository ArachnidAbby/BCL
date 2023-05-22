from typing import Any

from llvmlite import ir  # type: ignore

from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition


class Literal(ExpressionNode):
    __slots__ = ('value', 'ptr')
    isconstant = True

    def __init__(self, pos: SrcPosition, value: Any, typ):
        super().__init__(pos)
        self.value = value
        self.ret_type = typ

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)

    def __str__(self) -> str:
        return str(self.value)

    def repr_as_tree(self) -> str:
        return self.create_tree("Literal",
                                content=self.value,
                                return_type=self.ret_type)
