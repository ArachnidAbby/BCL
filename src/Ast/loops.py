import errors

from Ast.nodetypes import NodeTypes
from Ast.variable import VariableAssign

from . import Ast_Types
from .nodes import ASTNode, Block


class WhileStatement(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('cond', 'block', 'loop_before', 'while_after', 'while_body')

    name = "While"
    type = NodeTypes.STATEMENT

    def init(self, cond: ASTNode, block: Block):
        self.cond = cond
        self.block = block
        self.loop_before = None
        self.while_after = None
        self.while_body = None
    
    def pre_eval(self, func):
        self.cond.pre_eval(func)
        self.block.pre_eval(func)
    
    def eval(self, func):
        # cond = self.cond.eval(func)
        orig_block_name = func.builder.block._name
        self.while_body = func.builder.append_basic_block(f'{orig_block_name}.while')
        self.while_after = func.builder.append_basic_block(f'{orig_block_name}.endwhile')
        ret_bfor = func.has_return
        loop_bfor = func.inside_loop
        self.loop_before = loop_bfor

        func.inside_loop = self

        # # alloca outside of the loop body in order to not have a stack overflow!
        # for c,x in enumerate(self.block.children):
        #     if isinstance(x, VariableAssign) and x.is_declaration:
        #         variable = self.block.get_variable(x.var_name)
        #         if not self.block.validate_variable(x.var_name):
        #             variable.define(func, x.var_name)
        
        # branching and loop body

        self.branch_logic(func)
        func.builder.position_at_start(self.while_body)

        self.block.eval(func)
        if not func.has_return and not self.block.ended:
            self.branch_logic(func)

        func.has_return = ret_bfor
        func.inside_loop = loop_bfor

        func.builder.position_at_start(self.while_after)

        if func.block.last_instruction:
            func.builder.unreachable()
        
    
    def branch_logic(self, func):
        cond = self.cond.eval(func)
        func.builder.cbranch(cond, self.while_body, self.while_after)

class ContinueStatement(ASTNode):
    __slots__ = ()
    type = NodeTypes.STATEMENT
    name = "continue"

    def eval(self, func):
        if func.inside_loop is None:
            errors.error("Cannot use 'continue' outside of loop scope", line = self.position)
        
        Block.BLOCK_STACK[-1].ended = True
        func.inside_loop.branch_logic(func)
class BreakStatement(ASTNode):
    __slots__ = ()
    type = NodeTypes.STATEMENT
    name = "break"

    def eval(self, func):
        if func.inside_loop is None:
            errors.error("Cannot use 'break' outside of loop scope", line = self.position)
        
        Block.BLOCK_STACK[-1].ended = True
        func.builder.branch(func.inside_loop.while_after)
