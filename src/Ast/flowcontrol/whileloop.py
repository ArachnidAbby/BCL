class WhileStatement(ASTNode):
    '''Code for an If-Statement'''
    __slots__ = ('cond', 'block', 'loop_before', 'while_after', 'while_body')

    # name = "While"
    # type = NodeTypes.STATEMENT

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