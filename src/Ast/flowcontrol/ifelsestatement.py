from Ast.flowcontrol.ifstatement import IfStatement
from Ast.functions.returnstatement import ReturnStatement
from Ast.nodes import ASTNode, Block
from Ast.nodes.commontypes import SrcPosition


class IfElseStatement(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('cond', 'if_block', 'else_block')
    # type = NodeTypes.STATEMENT
    # name = "IfElse"

    def __init__(self, pos: SrcPosition, cond: ASTNode, if_block: ASTNode, else_block: ASTNode):
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
        cond = self.cond.eval(func)
        bfor = func.has_return
        with func.builder.if_else(cond) as (if_block, else_block):
            with if_block:
                for node in self.iter_block_or_stmt(self.if_block):
                    node.eval(func)
                    if isinstance(node, ReturnStatement):
                        func.has_return = bfor
            with else_block:
                if isinstance(self.else_block, IfStatement) and isinstance(self.else_block, IfElseStatement):
                    func.has_return = bfor
                self.else_block.eval(func)

        if func.block.last_instruction:
            func.builder.unreachable()
