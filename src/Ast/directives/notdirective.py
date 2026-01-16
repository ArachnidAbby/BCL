import errors
from Ast.directives.basedirective import CompilerDirective

usage_note = f"Example: {errors.RESET}Not(Platform(\"Windows\"))"


class NotDirective(CompilerDirective):
    __slots__ = ("directive_arg")

    def __init__(self, pos, args, original_stmt, module):
        super().__init__(pos, args, original_stmt, module)

        if len(args) != 1:
            errors.error("Invalid number of arguments, expects 1",
                         note=usage_note,
                         line=args.position)

        from . import directivenode

        self.directive_arg = directivenode.names_to_directives(args.children, module, original_stmt)[0]

    @property
    def should_compile(self):
        return not self.directive_arg.should_compile
