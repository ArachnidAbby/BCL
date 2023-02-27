from Ast.nodes import ASTNode, Block
from Ast.nodes.commontypes import SrcPosition


class IfElseStatement(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('cond', 'if_block', 'else_block')

    def __init__(self, pos: SrcPosition, cond: ASTNode, if_block: ASTNode,
                 else_block: ASTNode):
        self._position = pos
        self.cond = cond
        self.if_block = if_block
        self.else_block = else_block

    def pre_eval(self, func):
        self.cond.pre_eval(func)
        self.if_block.pre_eval(func)
        self.else_block.pre_eval(func)

    def iter_block_or_stmt(self, obj):
        if isinstance(self.if_block, Block):
            return self.iter_block(obj)

        return self.iter_stmt(obj)

    def iter_stmt(self, obj):
        yield obj

    def iter_block(self, obj):
        Block.BLOCK_STACK.append(obj)
        yield from obj.children
        Block.BLOCK_STACK.pop()

    def eval(self, func):
        cond = self.cond.ret_type.truthy(func, self.cond)
        bfor = func.has_return
        ifreturns = False
        elsereturns = False
        with func.builder.if_else(cond) as (if_block, else_block):
            with if_block:
                for node in self.iter_block_or_stmt(self.if_block):
                    node.eval(func)
                ifreturns = func.has_return
            func.has_return = bfor
            with else_block:
                self.else_block.eval(func)
                elsereturns = func.has_return

        if elsereturns and ifreturns:
            func.has_return = True
        else:
            func.has_return = bfor

        if func.block.last_instruction:
            func.builder.unreachable()

    def repr_as_tree(self) -> str:
        return self.create_tree("If Statement",
                                condition=self.cond,
                                contents_if=self.if_block,
                                contents_else=self.else_block)
