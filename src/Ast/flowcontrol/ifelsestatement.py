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
        ifreturns = False
        elsereturns = False
        with func.builder.if_else(cond) as (if_block, else_block):
            with if_block:
                for node in self.iter_block_or_stmt(self.if_block):
                    node.eval(func)
                    # if isinstance(node, ReturnStatement):
                    #     func.has_return = bfor
                ifreturns = func.has_return
            func.has_return = bfor
            with else_block:
                self.else_block.eval(func)
                # if isinstance(self.else_block, IfStatement):# or isinstance(self.else_block, IfElseStatement):
                #     func.has_return = bfor
                elsereturns = func.has_return

        if elsereturns and ifreturns:
            func.has_return = True
        else:
            func.has_return = bfor

        if func.block.last_instruction:
            func.builder.unreachable()
    # def eval(self, func):
    #     cond = self.cond.eval(func)
    #     bfor = func.has_return
    #     if_returns = False
    #     else_returns = False
    #     orig_block_name = func.builder.block._name
    #     ifbody = func.builder.append_basic_block(
    #             f'{orig_block_name}.if'
    #         )
    #     elsebody = func.builder.append_basic_block(
    #             f'{orig_block_name}.else'
    #         )
    #     ifend = func.builder.append_basic_block(
    #             f'{orig_block_name}.endif'
    #         )
    #     ifended = False
    #     else_ended = False
    #     func.builder.cbranch(cond, ifbody, elsebody)
    #     func.builder.position_at_start(ifbody)
    #     for node in self.iter_block_or_stmt(self.if_block):
    #         node.eval(func)
    #         if isinstance(node, ReturnStatement):
    #             if_returns = True
    #         ifended = Block.BLOCK_STACK[-1].ended
    #     if self.empty_block(self.if_block):
    #         func.builder.unreachable()
    #         self.if_block.ended = True

    #     if not isinstance(self.if_block, Block) or not ifended:
    #         print(str(func.module.module))
    #         print(Block.BLOCK_STACK[-1].ended)
    #         func.builder.branch(ifend)

    #     func.builder.position_at_start(elsebody)
    #     for node in self.iter_block_or_stmt(self.else_block):
    #         node.eval(func)
    #         if isinstance(node, ReturnStatement):
    #             else_returns = True
    #         else_ended = Block.BLOCK_STACK[-1].ended
    #     if self.empty_block(self.else_block):
    #         func.builder.unreachable()
    #         self.else_block.ended = True
    #     # if isinstance(self.else_block, IfStatement) and isinstance(self.else_block, IfElseStatement):
    #     #     func.has_return = bfor
    #     if not isinstance(self.else_block, Block) or not else_ended:
    #         func.builder.branch(ifend)

    #     if if_returns and else_returns:
    #         func.has_return = True
    #         print(if_returns, else_returns)
    #     else:
    #         func.has_return = bfor

    #     func.builder.position_at_start(ifend)

    #     if func.block.last_instruction:
    #         func.builder.unreachable()