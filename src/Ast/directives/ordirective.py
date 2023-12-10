from Ast.directives.basedirective import CompilerDirective


class OrDirective(CompilerDirective):
    __slots__ = ("directive_args",)

    def __init__(self, pos, args, original_stmt, module):
        super().__init__(pos, args, original_stmt, module)

        from . import directivenode

        self.directive_args = directivenode.names_to_directives(args.children,
                                                                module,
                                                                original_stmt)

    @property
    def should_compile(self):
        return any((x.should_compile for x in self.directive_args))
