from Ast.nodetypes import NodeTypes
from Ast.variable import VariableAssign

from . import Ast_Types
from .nodes import ASTNode, Block


class WhileStatement(ASTNode):
    '''Code for an If-Statement'''

    __slots__ = ('cond', 'block')

    name = "While"
    type = NodeTypes.STATEMENT

    def init(self, cond: ASTNode, block: Block):
        self.cond = cond
        self.block = block
    
    def pre_eval(self):
        self.cond.pre_eval()
        self.block.pre_eval()
    
    def eval(self, func):
        cond = self.cond.eval(func)
        orig_block_name = func.builder.block._name
        while_body = func.builder.append_basic_block(f'{orig_block_name}.while.body')
        while_after = func.builder.append_basic_block(f'{orig_block_name}.while.after')

        # alloca outside of the loop body in order to not have a stack overflow!
        for c,x in enumerate(self.block.children):
            if isinstance(x, VariableAssign) and x.is_declaration:
                variable = self.block.get_variable(x.name)
                if not self.block.validate_variable(x.name):
                    ptr = func.builder.alloca(self.block.get_variable(x.name).type.ir_type, name=x.name)
                    variable.ptr = ptr
        
        # branching and loop body

        func.builder.cbranch(cond, while_body, while_after)
        func.builder.position_at_start(while_body)

        self.block.eval(func)
        cond = self.cond.eval(func)
        func.builder.cbranch(cond, while_body, while_after)

        func.builder.position_at_start(while_after)
