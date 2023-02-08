from llvmlite import ir

from Ast import Ast_Types
from Ast.literals.numberliteral import Literal
from Ast.nodes import ASTNode, Block
from Ast.nodes.commontypes import SrcPosition
from Ast.variables.varobject import VariableObj


class ForLoop(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('var', 'rang', 'block', 'loop_before', 'for_after',
                 'for_body', 'varptr',)

    # name = "forloop"
    # type = NodeTypes.STATEMENT

    def __init__(self, pos: SrcPosition, var: ASTNode, rang, block: Block):
        super().__init__(pos)
        self.var = var
        self.varptr = None
        self.rang = rang
        self.block = block
        self.loop_before = None
        self.for_after = None
        self.for_body = None

    def pre_eval(self, func):
        self.varptr = func.create_const_var(Ast_Types.Integer_32())
        self.block.variables[self.var.var_name] = VariableObj(self.varptr, Ast_Types.Integer_32(), False)

        if self.rang.start.constant and self.rang.end.constant:
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
