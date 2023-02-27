import errors
from Ast.nodes import ASTNode, Block


class BreakStatement(ASTNode):
    __slots__ = ()

    def eval(self, func):
        if func.inside_loop is None:
            errors.error("Cannot use 'break' outside of loop scope",
                         line=self.position)

        Block.BLOCK_STACK[-1].ended = True
        func.builder.branch(func.inside_loop.while_after)

    def repr_as_tree(self) -> str:
        return "Break Statement"
