from Ast.nodes.expression import ExpressionNode


class PassNode(ExpressionNode):
    '''Pass a llvm instruction as a node directly'''

    __slots__ = ('instr', 'ret_type')

    def __init__(self, pos, instr, typ):
        super().__init__(pos)
        self.instr = instr
        self.ret_type = typ

    def eval(self, func):
        return self.instr
