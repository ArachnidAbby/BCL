import errors
from Ast.directives.basedirective import CompilerDirective
from Ast.literals import stringliteral


class NotDirective(CompilerDirective):
    __slots__ = ("directive_arg")

    def __init__(self, pos, args, original_stmt, module):
        from Ast import enumdef
        from Ast.structs import StructDef

        super().__init__(pos, args, original_stmt, module)

        if len(args) != 1:
            errors.error("Invalid number of arguments, expects 1",
                         line=args.position)

        from . import directivenode

        self.directive_arg = directivenode.names_to_directives(args.children, module, original_stmt)[0]  # remove 0x00 char

    @property
    def should_compile(self):
        return not self.directive_arg.should_compile

    # def _do_platform_check(self, func, node_func):
    #     if platform.system().lower() == self.platform:
    #         return func(node_func)
    #     return None

    # def fullfill_templates(self, func):
    #     return self._do_platform_check(
    #         self.passed_stmt.fullfill_templates,
    #         func
    #     )

    # def post_parse(self, func):
    #     return self._do_platform_check(
    #         self.passed_stmt.post_parse,
    #         func
    #     )

    # def pre_eval(self, func):
    #     return self._do_platform_check(
    #         self.passed_stmt.pre_eval,
    #         func
    #     )

    # def eval_impl(self, func):
    #     return self._do_platform_check(
    #         self.passed_stmt.eval_impl,
    #         func
    #     )