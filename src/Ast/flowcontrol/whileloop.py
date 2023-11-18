from Ast.nodes import ASTNode, Block
from Ast.nodes.commontypes import SrcPosition


class WhileStatement(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('cond', 'block', 'loop_before', 'while_after', 'while_body')

    def __init__(self, pos: SrcPosition, cond: ASTNode, block: Block):
        super().__init__(pos)
        self.cond = cond
        self.block = block
        self.loop_before = None
        self.while_after = None
        self.while_body = None

    def copy(self):
        out = WhileStatement(self._position, self.cond.copy(),
                             self.block.copy())
        return out

    def fullfill_templates(self, func):
        self.block.fullfill_templates(func)
        self.cond.fullfill_templates(func)

    def post_parse(self, func):
        self.block.post_parse(func)
        self.cond.post_parse(func)
        # for child in self.block:
        #     child.post_parse(func)

    def pre_eval(self, func):
        self.cond.pre_eval(func)
        self.block.pre_eval(func)

    @property
    def loop_after(self):
        return self.while_after

    def eval_impl(self, func):
        # cond = self.cond.eval(func)
        orig_block_name = func.builder.block._name
        body_name = f'{orig_block_name}.while'
        end_name = f'{orig_block_name}.endwhile'
        self.while_body = func.builder.append_basic_block(body_name)
        self.while_after = func.builder.append_basic_block(end_name)
        ret_before = func.has_return
        self.loop_before = func.inside_loop
        func.inside_loop = self

        # branching and loop body
        self.branch_logic(func)
        func.builder.position_at_start(self.while_body)

        self.block.eval(func)
        if not func.has_return and not self.block.ended:
            self.branch_logic(func)

        func.has_return = ret_before
        func.inside_loop = self.loop_before

        func.builder.position_at_start(self.while_after)

        if func.block.last_instruction:
            func.builder.unreachable()

    # ! Must be shared between both kinds of loop !
    def branch_logic(self, func):
        cond = self.cond.ret_type.truthy(func, self.cond)
        func.builder.cbranch(cond, self.while_body, self.while_after)

    def repr_as_tree(self) -> str:
        return self.create_tree("For Loop",
                                condition=self.cond,
                                contents=self.block)
