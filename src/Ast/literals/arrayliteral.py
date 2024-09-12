
from typing import Any

from llvmlite import ir

import errors
from Ast import Ast_Types
from Ast.literals.numberliteral import Literal
from Ast.nodes import ExpressionNode
from Ast.nodes.block import create_const_var, get_current_block
from Ast.nodes.commontypes import Lifetimes, SrcPosition
from Ast.nodes.passthrough import PassNode  # type: ignore


class ArrayLiteral(ExpressionNode):
    __slots__ = ('value', 'literal', 'repeat')
    isconstant = False

    def __init__(self, pos: SrcPosition, value: list[Any], repeat=None):
        super().__init__(pos)
        self.value = value
        self.ptr = None
        self.repeat = repeat
        # whether or not this array is only full of literals
        self.literal = True

    def copy(self):
        out = ArrayLiteral(self._position, [val.copy() for val in self.value], self.repeat)
        return out

    def fullfill_templates(self, func):
        for x in self.value:
            x.fullfill_templates(func)

    def post_parse(self, func):
        for x in self.value:
            x.post_parse(func)

    def pre_eval(self, func):
        self.value[0].pre_eval(func)
        typ = self.value[0].ret_type

        if self.repeat is not None:
            amount = self.repeat.get_var(func)
            amount.pre_eval(func)
            if not self.repeat.isconstant or \
                    not isinstance(self.repeat.ret_type, Ast_Types.Integer_32):
                errors.error("Array literal size must be an i32",
                             line=self.position)

            if amount.value <= 0:
                errors.error("Array literal size must be greater than '0'",
                             line=self.position)
            self.value = self.value * amount.value
            self.repeat = None

        for x in self.value:
            x.pre_eval(func)
            if x.ret_type != typ:
                errors.error(f"Invalid type '{x.ret_type}' in a list of type" +
                             f" '{typ}'", line=x.position)
            self.literal = self.literal and x.isconstant

        array_size = Literal(SrcPosition.invalid(), len(self.value),
                             Ast_Types.Integer_32())
        self.ret_type = Ast_Types.Array(array_size, typ)

    def eval_impl(self, func):
        # Allocate for array and then munually
        # populate items if it isn't an array
        # of literal values.
        if not self.literal:
            ptr = create_const_var(func, self.ret_type)
            zero_const = ir.Constant(ir.IntType(64), 0)
            for c, item in enumerate(self.value):
                index = ir.Constant(ir.IntType(32), c)
                item_ptr = func.builder.gep(ptr, [zero_const, index])
                # item.overwrite_eval = True
                evaled = item.eval(func)
                if item.do_register_dispose and item.ret_type.needs_dispose:
                    dispose_node = PassNode(item.position, evaled,
                                            item.ret_type, item.ptr)
                    get_current_block().register_dispose(func, dispose_node)

                item.ptr = None
                item._instruction = evaled
                func.builder.store(evaled, item_ptr)
                node = PassNode(item.position, evaled, item.ret_type, item_ptr)

                item.ret_type.add_ref_count(func, node)
            self.ptr = ptr
            return func.builder.load(ptr)

        return ir.Constant.literal_array([x.eval(func) for x in self.value])

    def as_type_reference(self, func, allow_generics=False):
        from Ast.Ast_Types.Type_Slice import SliceType
        if len(self.value) != 1:
            errors.error("Invalid Type signature", line=self.position)

        inner_type = self.value[0].as_type_reference(func, allow_generics)
        return SliceType(inner_type)

    def get_lifetime(self, func):
        return Lifetimes.FUNCTION

    def get_position(self) -> SrcPosition:
        x = self.merge_pos([x.position for x in self.value])  # type: ignore
        return SrcPosition(x.line, x.col, x.length+1, x.source_name)

    def repr_as_tree(self) -> str:
        return self.create_tree("Array Literal",
                                content=self.value,
                                size=self.ret_type.size,
                                return_type=self.ret_type)
