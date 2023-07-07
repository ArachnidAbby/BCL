from Ast.nodes.expression import ExpressionNode


class PassNode(ExpressionNode):
    '''Pass a llvm instruction as a node directly'''

    __slots__ = ('instr', 'ret_type')
    do_register_dispose = False

    def __init__(self, pos, instr, typ, ptr=None):
        super().__init__(pos)
        self.instr = instr
        self.ret_type = typ
        self.ptr = ptr

    def eval_impl(self, func):
        return self.instr
