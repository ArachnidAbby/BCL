from Ast import Ast_Types
from Ast.nodetypes import NodeTypes

from .nodes import ASTNode


class IfStatement(ASTNode):
    '''Code for an If-Statement'''

    __slots__ = ('cond', 'block')
    type = NodeTypes.STATEMENT

    def init(self, cond: ASTNode, block: ASTNode):
        self.name = "If"

        self.cond = cond
        self.block = block
    
    def pre_eval(self):
        self.cond.pre_eval()
        self.block.pre_eval()
    
    def eval(self, func):
        cond = self.cond.eval(func)
        with func.builder.if_then(cond) as if_block:
            self.block.eval(func)

class IfElseStatement(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('cond', 'if_block', 'else_block')
    type = NodeTypes.STATEMENT

    def init(self, cond: ASTNode, if_block: ASTNode, else_block: ASTNode):
        self.name = "IfElse"

        self.cond = cond
        self.if_block = if_block
        self.else_block = else_block
    
    def pre_eval(self):
        self.cond.pre_eval()
        self.if_block.pre_eval()
        self.else_block.pre_eval()

    def eval(self, func):
        cond = self.cond.eval(func)
        with func.builder.if_else(cond) as (if_block, else_block):
            with if_block:
                self.if_block.eval(func)
            with else_block:
                self.else_block.eval(func)
        