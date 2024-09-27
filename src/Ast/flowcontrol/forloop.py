from typing import TYPE_CHECKING

from Ast.nodes import ASTNode, Block
from Ast.nodes.block import create_const_var
from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.passthrough import PassNode
from Ast.variables.varobject import VariableObj

if TYPE_CHECKING:
    from Ast.variables.reference import VariableRef


class ForLoop(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('var', 'iterable', 'block', 'loop_before', 'for_after',
                 'for_body', 'varptr', 'iter_ptr', 'iter_type', 'for_pre_body')

    def __init__(self, pos: SrcPosition, var: "VariableRef", iterable,
                 block: Block):
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
        self.for_pre_body = None

    def copy(self):
        out = ForLoop(self._position, self.var.copy(), self.iterable.copy(),
                      self.block.copy())
        return out

    def fullfill_templates(self, func):
        self.block.fullfill_templates(func)
        self.iterable.fullfill_templates(func)

    def post_parse(self, func):
        self.block.post_parse(func)
        self.iterable.post_parse(func)

    def pre_eval(self, func):
        self.iterable.pre_eval(func)

        self.iter_type = self.iterable.ret_type

        if not self.iterable.ret_type.is_iterator:
            self.iter_type = self.iter_type.get_iter_return(func,
                                                            self.iterable)

        self.block.variables[self.var.var_name] = \
            VariableObj(None,
                        self.iter_type.get_iter_return(func, self.iterable),
                        False)

        self.block.pre_eval(func)

    @property
    def loop_after(self):
        return self.for_after

    def eval_impl(self, func):
        orig_block_name = func.builder.block._name
        iter_ret_typ = self.iter_type.get_iter_return(func, self.iterable)
        self.varptr = create_const_var(func, iter_ret_typ)
        if iter_ret_typ.needs_dispose:
            node = PassNode(self.var.position, None, iter_ret_typ,
                            ptr=self.varptr)
            self.block.register_dispose(func, node)
        self.block.variables[self.var.var_name].ptr = self.varptr

        # Handles calling of destructors on subsequent iterations
        self.for_pre_body = func.builder.append_basic_block(
                f'{orig_block_name}.for_pre'
            )
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
            self.iter_ptr = iter_ret.create_iterator(func, self.iterable,
                                                     self.iterable.position)
        else:
            self.iterable.eval(func)
            self.iter_ptr = self.iterable.get_ptr(func)

        func.builder.store(self.iter_type.iter_get_val(func, self.iter_ptr,
                                                       self.iterable.position),
                           self.varptr)

        # branching and loop body
        cond = self.iter_type.iter_condition(func, self.iter_ptr,
                                             self.iterable.position)
        func.builder.cbranch(cond, self.for_body, self.for_after)
        func.builder.position_at_start(self.for_body)

        self.block.eval(func)

        if not func.has_return and not self.block.ended:
            self.branch_logic(func)

        # create pre_body
        func.builder.position_at_start(self.for_pre_body)
        for node in self.block.dispose_queue:
            node.ret_type.dispose(func, node)
        func.builder.branch(self.for_body)

        # exit loop
        func.inside_loop = loop_bfor
        func.has_return = ret_before
        func.builder.position_at_start(self.for_after)

        if func.block.last_instruction:
            func.builder.unreachable()

    # ! Must be shared between both kinds of loop !
    def branch_logic(self, func):
        func.builder.store(self.iter_type.iter(func, self.iter_ptr,
                                               self.iterable.position),
                           self.varptr)
        cond = self.iter_type.iter_condition(func, self.iter_ptr,
                                             self.iterable.position)
        func.builder.cbranch(cond, self.for_pre_body, self.for_after)

    def repr_as_tree(self) -> str:
        return self.create_tree("For Loop",
                                var=self.block.variables[self.var.var_name],
                                range=self.iterable,
                                contents=self.block)
