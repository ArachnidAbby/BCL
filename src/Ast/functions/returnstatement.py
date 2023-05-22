from llvmlite import ir

import errors
from Ast.nodes import ASTNode, ExpressionNode
from Ast.nodes.block import Block
from Ast.nodes.commontypes import SrcPosition


class ReturnStatement(ASTNode):
    __slots__ = ('expr')

    def __init__(self, pos: SrcPosition, expr: ExpressionNode):
        self._position = pos
        self.expr = expr

    def pre_eval(self, func):
        if self.expr is None:
            return
        self.expr.pre_eval(func)

    def _check_valid_type(self, func):
        if func.ret_type.is_void() or func.yields:
            if self.expr is None:
                return
            errors.error("Return value of function is \"Void\", " +
                         "use \"return;\" instead",
                         line=self.position)
        if self.expr.ret_type != func.ret_type:
            errors.error(f"Function, \"{func.func_name}\", has a return type" +
                         f" of '{func.ret_type}'. Return statement returned" +
                         f" '{self.expr.ret_type}'", line=self.position)

    def eval(self, func):
        func.has_return = True
        self._check_valid_type(func)

        if func.yields:
            continue_ptr = func.builder.gep(func.yield_struct_ptr,
                                            [ir.Constant(ir.IntType(32), 0),
                                             ir.Constant(ir.IntType(32), 0)])
            func.builder.store(ir.Constant(ir.IntType(1), 0), continue_ptr)

        if func.ret_type.is_void():
            func.builder.ret_void()
        else:
            func.builder.ret(self.expr.eval(func))
        Block.BLOCK_STACK[-1].ended = True

    def repr_as_tree(self) -> str:
        return self.create_tree("Return Statement",
                                contents=self.expr)

    def get_position(self):
        if self.expr is None:
            return self._position
        return self.merge_pos((self._position, self.expr.position))
