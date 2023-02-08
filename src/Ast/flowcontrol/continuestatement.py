import errors
from Ast.nodes import ASTNode, Block


class ContinueStatement(ASTNode):
    __slots__ = ()
    # type = NodeTypes.STATEMENT
    # name = "continue"

    def eval(self, func):
        if func.inside_loop is None:
            errors.error("Cannot use 'continue' outside of loop scope", line=self.position)

        Block.BLOCK_STACK[-1].ended = True
        func.inside_loop.branch_logic(func)
