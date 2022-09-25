from Ast import Ast_Types
from Ast.Node_Types import NodeTypes

from .Nodes import AST_NODE


class IfStatement(AST_NODE):
    '''Code for an If-Statement'''

    __slots__ = ('cond', 'block')

    def init(self, cond: AST_NODE, block: AST_NODE):
        self.name = "If"
        self.type = NodeTypes.STATEMENT
        self.ret_type = Ast_Types.Void()

        self.cond = cond
        self.block = block
    
    def pre_eval(self):
        self.cond.pre_eval()
        self.block.pre_eval()
    
    def eval(self, func):
        cond = self.cond.eval(func)
        with func.builder.if_then(cond) as if_block:
            self.block.eval(func)

class IfElseStatement(AST_NODE):
    '''Code for an If-Statement'''
    __slots__ = ('cond', 'if_block', 'else_block')

    def init(self, cond: AST_NODE, if_block: AST_NODE, else_block: AST_NODE):
        self.name = "IfElse"
        self.type = NodeTypes.STATEMENT
        self.ret_type = Ast_Types.Void()

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
        