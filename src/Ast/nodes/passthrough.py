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

    # def get_ptr(self, func):
    #     if self.ptr is None:
    #         super().get_ptr(func)
    #     return self.ptr


class CallbackPassNode(ExpressionNode):
    '''Pass a llvm instruction (by using callbacks)
    as a node directly'''

    __slots__ = ('instr_callback', 'ptr_callback', 'ret_type')
    do_register_dispose = False

    def __init__(self, pos, instr, typ, ptr=None):
        super().__init__(pos)
        self.instr_callback = instr
        self.ret_type = typ
        self.ptr_callback = ptr

    def eval_impl(self, func):
        return self.instr_callback()

    def get_ptr(self, func):
        if self.ptr_callback is None:
            return super().get_ptr(func)
        return self.ptr_callback()
