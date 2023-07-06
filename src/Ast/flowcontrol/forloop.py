from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.nodes import ASTNode, Block
from Ast.nodes.commontypes import SrcPosition
from Ast.variables.varobject import VariableObj


class ForLoop(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('var', 'iterable', 'block', 'loop_before', 'for_after',
                 'for_body', 'varptr', 'iter_ptr', 'iter_type')

    def __init__(self, pos: SrcPosition, var: ASTNode, iterable, block: Block):
        super().__init__(pos)
        self.var = var
        self.varptr = None
        self.iterable = iterable
        self.iter_type = None
        self.iter_ptr = None
        self.block = block
        self.loop_before = None
        self.for_after = None
        self.for_body = None

    def post_parse(self, func):
        for child in self.block:
            child.post_parse(func)

    def pre_eval(self, func):
        self.iterable.pre_eval(func)

        if self.iterable.ret_type.is_iterator:
            self.iter_type = self.iterable.ret_type
        else:
            self.iter_type = self.iterable.ret_type.get_iter_return(self.iterable.position)

        self.block.variables[self.var.var_name] = \
            VariableObj(None,
                        self.iter_type.get_iter_return(self.iterable.position),
                        False)

        self.block.pre_eval(func)

    def eval_impl(self, func):
        orig_block_name = func.builder.block._name
        self.varptr = func.create_const_var(self.iter_type.get_iter_return(self.iterable.position))
        self.block.variables[self.var.var_name].ptr = self.varptr
        self.for_body = func.builder.append_basic_block(
                f'{orig_block_name}.for'
            )
        self.for_after = func.builder.append_basic_block(
                f'{orig_block_name}.endfor'
            )
        loop_bfor = func.inside_loop
        self.loop_before = loop_bfor
        func.inside_loop = self

        ret_before = func.has_return

        # create cond
        if not self.iterable.ret_type.is_iterator:
            iter_ret = self.iterable.ret_type
            self.iter_ptr = iter_ret.create_iterator(func, self.iterable, self.iterable.position)
        else:
            self.iterable.eval(func)
            self.iter_ptr = self.iterable.get_ptr(func)

        func.builder.store(self.iter_type.iter_get_val(func, self.iter_ptr, self.iterable.position),
                           self.varptr)

        # branching and loop body
        cond = self.iter_type.iter_condition(func, self.iter_ptr, self.iterable.position)
        func.builder.cbranch(cond, self.for_body, self.for_after)
        func.builder.position_at_start(self.for_body)

        self.block.eval(func)

        if not func.has_return and not self.block.ended:
            self.branch_logic(func)

        func.inside_loop = loop_bfor
        func.has_return = ret_before
        func.builder.position_at_start(self.for_after)

        if func.block.last_instruction:
            func.builder.unreachable()

    def branch_logic(self, func):
        func.builder.store(self.iter_type.iter(func, self.iter_ptr, self.iterable.position),
                           self.varptr)
        cond = self.iter_type.iter_condition(func, self.iter_ptr, self.iterable.position)
        func.builder.cbranch(cond, self.for_body, self.for_after)

    def repr_as_tree(self) -> str:
        return self.create_tree("For Loop",
                                var=self.block.variables[self.var.var_name],
                                range=self.iterable,
                                contents=self.block)
