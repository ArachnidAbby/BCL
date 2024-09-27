from Ast.nodes.astnode import ASTNode


class CompilerDirective(ASTNode):
    __slots__ = ("original_stmt", "args", "passed_stmt", "module")

    def __init__(self, pos, args, original_stmt, module):
        super().__init__(pos)

        self.original_stmt = original_stmt
        self.passed_stmt = None
        self.args = args
        self.module = module

    def copy(self, stmt):
        return self.__class__(self._position,
                              self.args.copy(),
                              stmt,
                              self.module)

    @property
    def should_compile(self):
        '''say if it should compile the given thing'''
        return True

    def reset(self):
        self.passed_stmt.reset()

    def fullfill_templates(self, func):
        self.passed_stmt.fullfill_templates(func)

    def post_parse(self, func):
        self.passed_stmt.post_parse(func)

    def pre_eval(self, func):
        self.passed_stmt.pre_eval(func)

    def eval_impl(self, func):
        self.passed_stmt.eval_impl(func)

    # def get_position(self):
    #     return self.passed_stmt.get_position()
