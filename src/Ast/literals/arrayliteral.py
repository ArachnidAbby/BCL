
from typing import Any

from llvmlite import ir  # type: ignore

import errors
from Ast import Ast_Types
from Ast.literals.numberliteral import Literal
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition


class ArrayLiteral(ExpressionNode):
    __slots__ = ('value', 'ir_type', 'literal')
    isconstant = False

    def __init__(self, pos: SrcPosition, value: list[Any]):
        super().__init__(pos)
        self.value = value
        self.ptr = None
        # whether or not this array is only full of literals
        self.literal = True

    def pre_eval(self, func):
        self.value[0].pre_eval(func)
        typ = self.value[0].ret_type

        for x in self.value:
            x.pre_eval(func)
            if x.ret_type != typ:
                errors.error(f"Invalid type '{x.ret_type}' in a list of type" +
                             f" '{typ}'", line=x.position)
            self.literal = self.literal and x.isconstant

        array_size = Literal(SrcPosition.invalid(), len(self.value),
                             Ast_Types.Integer_32())
        self.ret_type = Ast_Types.Array(array_size, typ)
        self.ir_type = self.ret_type.ir_type

    def eval(self, func):
        # Allocate for array and then munually
        # populate items if it isn't an array
        # of literal values.
        if not self.literal:
            ptr = func.create_const_var(self.ret_type)
            zero_const = ir.Constant(ir.IntType(64), 0)
            for c, item in enumerate(self.value):
                index = ir.Constant(ir.IntType(32), c)
                item_ptr = func.builder.gep(ptr, [zero_const, index])
                func.builder.store(item.eval(func), item_ptr)
            self.ptr = ptr
            return func.builder.load(ptr)

        return ir.Constant.literal_array([x.eval(func) for x in self.value])

    def get_position(self) -> SrcPosition:
        x = self.merge_pos([x.position for x in self.value])  # type: ignore
        return SrcPosition(x.line, x.col, x.length+1, x.source_name)
