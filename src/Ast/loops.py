import errors
from llvmlite import ir

from Ast.nodetypes import NodeTypes
from Ast.variable import VariableAssign
from Ast.varobject import VariableObj

from . import Ast_Types
from .nodes import ASTNode, Block, SrcPosition


class WhileStatement(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('cond', 'block', 'loop_before', 'while_after', 'while_body')

    name = "While"
    type = NodeTypes.STATEMENT

    def __init__(self, pos: SrcPosition, cond: ASTNode, block: Block):
        super().__init__(pos)
        self.cond        = cond
        self.block       = block
        self.loop_before = None
        self.while_after = None
        self.while_body  = None
    
    def pre_eval(self, func):
        self.cond.pre_eval(func)
        self.block.pre_eval(func)
    
    def eval(self, func):
        # cond = self.cond.eval(func)
        orig_block_name  = func.builder.block._name
        self.while_body  = func.builder.append_basic_block(f'{orig_block_name}.while')
        self.while_after = func.builder.append_basic_block(f'{orig_block_name}.endwhile')
        ret_bfor         = func.has_return
        loop_bfor        = func.inside_loop
        self.loop_before = loop_bfor
        func.inside_loop = self
        
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

class ForLoop(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('var', 'rang', 'block', 'loop_before', 'for_after', 'for_body', 'varptr',)

    name = "While"
    type = NodeTypes.STATEMENT

    def __init__(self, pos: SrcPosition, var: ASTNode, rang, block: Block):
        super().__init__(pos)
        self.var         = var
        self.varptr      = None
        self.rang        = rang
        self.block       = block
        self.loop_before = None
        self.for_after   = None
        self.for_body    = None
    
    def pre_eval(self, func):
        self.varptr = func.create_const_var(Ast_Types.Integer_32())
        self.block.variables[self.var.var_name] = VariableObj(self.varptr, Ast_Types.Integer_32(), False)

        if self.rang.start.name == "literal" and self.rang.end.name=="literal":
            self.block.variables[self.var.var_name].range = (self.rang.start.value, self.rang.end.value)

        self.rang.pre_eval(func)
        self.block.pre_eval(func)
    
    def eval(self, func):
        # cond = self.cond.eval(func)
        orig_block_name = func.builder.block._name
        self.for_body = func.builder.append_basic_block(f'{orig_block_name}.for')
        self.for_after = func.builder.append_basic_block(f'{orig_block_name}.endfor')
        loop_bfor = func.inside_loop
        self.loop_before = loop_bfor
        func.inside_loop = self

        # create cond
        self.rang.eval(func)
        func.builder.store(self.rang.start, self.varptr)
        
        # branching and loop body
        func.builder.branch(self.for_body)
        func.builder.position_at_start(self.for_body)

        self.block.eval(func)
        if not func.has_return and not self.block.ended:
            self.branch_logic(func)

        func.inside_loop = loop_bfor
        func.builder.position_at_start(self.for_after)

        if func.block.last_instruction:
            func.builder.unreachable()
        
    
    def branch_logic(self, func):
        val = func.builder.load(self.varptr)
        val = func.builder.add(ir.Constant(ir.IntType(32), 1), val)
        func.builder.store(val, self.varptr)
        cond = func.builder.icmp_signed("<", val, self.rang.end)
        func.builder.cbranch(cond, self.for_body, self.for_after)

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
