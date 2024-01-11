import errors
from Ast.nodes import ASTNode
from Ast.nodes.block import get_current_block


class BreakStatement(ASTNode):
    __slots__ = ()

    def eval_impl(self, func):
        if func.inside_loop is None:
            errors.error("Cannot use 'break' outside of loop scope",
                         line=self.position)

        get_current_block().ended = True
        func.builder.branch(func.inside_loop.loop_after)

    def copy(self):
        return BreakStatement(self._position)

    def fullfill_templates(self, func):
        return super().fullfill_templates(func)

    def repr_as_tree(self) -> str:
        return "Break Statement"
