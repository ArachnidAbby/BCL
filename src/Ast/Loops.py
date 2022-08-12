from llvmlite import ir

from .Nodes import AST_NODE

class WhileStatement(AST_NODE):
    '''Code for an If-Statement'''

    __slots__ = ['cond', 'block']

    def init(self, cond: AST_NODE, block: AST_NODE):
        self.name = "While"
        self.type = "statement"
        self.ret_type = "void"

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

        func.builder.cbranch(cond, while_body, while_after)
        func.builder.position_at_start(while_body)

        self.block.eval(func)
        cond = self.cond.eval(func)
        func.builder.cbranch(cond, while_body, while_after)

        func.builder.position_at_start(while_after)