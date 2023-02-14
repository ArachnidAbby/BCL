from Ast.nodes import ASTNode
from Ast.nodes.block import Block
from Ast.nodes.commontypes import SrcPosition


class IfStatement(ASTNode):
    '''Code for an If-Statement'''

    __slots__ = ('cond', 'block')

    def __init__(self, pos: SrcPosition, cond: ASTNode, block: ASTNode):
        self._position = pos
        self.cond = cond
        self.block = block

    def pre_eval(self, func):
        self.cond.pre_eval(func)
        self.block.pre_eval(func)

    def eval(self, func):
        cond = self.cond.eval(func)
        bfor = func.has_return

        with func.builder.if_then(cond):
            self.block.eval(func)
            func.has_return = bfor

        if Block.BLOCK_STACK[-1].ended:
            func.builder.unreachable()
