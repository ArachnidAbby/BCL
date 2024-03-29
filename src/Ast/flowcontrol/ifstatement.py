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

    def copy(self):
        out = IfStatement(self._position, self.cond.copy(), self.block.copy())
        return out

    def fullfill_templates(self, func):
        self.block.fullfill_templates(func)
        self.cond.fullfill_templates(func)

    def post_parse(self, func):
        self.block.post_parse(func)
        self.cond.post_parse(func)
        # for child in self.block:
        #     child.post_parse(func)

    def pre_eval(self, func):
        self.cond.pre_eval(func)
        self.block.pre_eval(func)

    def eval_impl(self, func):
        cond = self.cond.ret_type.truthy(func, self.cond)
        bfor = func.has_return

        with func.builder.if_then(cond):
            self.block.eval(func)
            func.has_return = bfor

        if Block.BLOCK_STACK[-1].ended:
            func.builder.unreachable()

    def repr_as_tree(self) -> str:
        return self.create_tree("If Statement",
                                condition=self.cond,
                                contents=self.block)
