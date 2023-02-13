from Ast.nodes import ASTNode
from Ast.nodes.block import Block
from Ast.nodes.commontypes import SrcPosition


class IfStatement(ASTNode):
    '''Code for an If-Statement'''

    __slots__ = ('cond', 'block')
    # type = NodeTypes.STATEMENT
    # name = "If"

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

        with func.builder.if_then(cond) as if_block:  # TODO: REMOVE "as if_block"
            self.block.eval(func)
            func.has_return = bfor

        if Block.BLOCK_STACK[-1].ended:
            func.builder.unreachable()

    # def eval(self, func):
    #     cond = self.cond.eval(func)
    #     bfor = func.has_return
    #     ifended = False
    #     orig_block_name = func.builder.block._name
    #     ifbody = func.builder.append_basic_block(
    #             f'{orig_block_name}.if'
    #         )
    #     ifend = func.builder.append_basic_block(
    #             f'{orig_block_name}.endif'
    #         )

    #     func.builder.cbranch(cond, ifbody, ifend)
    #     func.builder.position_at_start(ifbody)
    #     for child in self.iter_stmts():
    #         child.eval(func)
    #         ifended = Block.BLOCK_STACK[-1].ended

    #     if not isinstance(self.block, Block) or not ifended:
    #         func.builder.branch(ifend)
    #     func.builder.position_at_start(ifend)

    #     func.has_return = bfor

    #     if func.block.last_instruction:
    #         func.builder.unreachable()