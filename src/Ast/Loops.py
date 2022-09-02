from llvmlite import ir
from Ast.Ast_Types.Utils import Types
from Ast.Node_Types import NodeTypes

from Ast.Variable import VariableAssign

from .Nodes import AST_NODE, Block

class WhileStatement(AST_NODE):
    '''Code for an If-Statement'''

    __slots__ = ('cond', 'block')

    def init(self, cond: AST_NODE, block: Block):
        self.name = "While"
        self.type = NodeTypes.STATEMENT
        self.ret_type = Types.VOID

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
            if isinstance(x, VariableAssign) and x.type == "variableDeclare":
                variable = self.block.get_variable(x.name)
                if not self.block.validate_variable(x.name):
                    ptr = func.builder.alloca(x.value.ir_type, name=x.name)
                    variable.ptr = ptr
        
        # branching and loop body

        func.builder.cbranch(cond, while_body, while_after)
        func.builder.position_at_start(while_body)

        self.block.eval(func)
        cond = self.cond.eval(func)
        func.builder.cbranch(cond, while_body, while_after)

        func.builder.position_at_start(while_after)