from llvmlite import ir
from Ast.nodes.passthrough import PassNode

import errors
from Ast.nodes import ASTNode, ExpressionNode
from Ast.nodes.block import Block
from Ast.nodes.commontypes import Lifetimes, SrcPosition


class ReturnStatement(ASTNode):
    __slots__ = ('expr')

    def __init__(self, pos: SrcPosition, expr: ExpressionNode):
        self._position = pos
        self.expr = expr

    def copy(self):
        if self.expr is None:
            expr_copy = None
        else:
            expr_copy = self.expr.copy()
        out = ReturnStatement(self._position, expr_copy)
        return out

    def fullfill_templates(self, func):
        if self.expr is None:
            return
        self.expr.fullfill_templates(func)

    def post_parse(self, func):
        if self.expr is None:
            return
        self.expr.post_parse(func)

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

    def eval_impl(self, func):
        func.has_return = True
        self._check_valid_type(func)

        if func.yields:
            continue_ptr = func.builder.gep(func.yield_struct_ptr,
                                            [ir.Constant(ir.IntType(32), 0),
                                             ir.Constant(ir.IntType(32), 0)])
            func.builder.store(ir.Constant(ir.IntType(1), 0), continue_ptr)

        ret_val = None
        if not func.ret_type.is_void():
            node = PassNode(self.expr.position, self.expr.eval(func), self.expr.ret_type)
            self.expr.ret_type.add_ref_count(func, node)
            ret_val = self.expr._instruction
            if self.expr.get_lifetime(func) != Lifetimes.LONG and not self.expr.ret_type.returnable:
                errors.error(f"{str(self.expr.ret_type)} is not returnable",
                             line=self.expr.position)

        func.dispose_stack()

        if func.ret_type.is_void():
            func.builder.ret_void()
        else:
            func.builder.ret(ret_val)
        Block.BLOCK_STACK[-1].ended = True

    def repr_as_tree(self) -> str:
        return self.create_tree("Return Statement",
                                contents=self.expr)

    def get_position(self):
        if self.expr is None:
            return self._position
        return self.merge_pos((self._position, self.expr.position))
