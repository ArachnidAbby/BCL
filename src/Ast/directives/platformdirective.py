import platform

import errors
from Ast.directives.basedirective import CompilerDirective
from Ast.literals import stringliteral

VALID_PLATFORMS = [
     "darwin",
     "windows",
     "linux"
]

usage_note = f"Example: {errors.RESET}Platform(\"Windows\")"


class PlatformDirective(CompilerDirective):
    __slots__ = ("platform",)

    def __init__(self, pos, args, original_stmt, module):
        super().__init__(pos, args, original_stmt, module)

        if len(args) != 1:
            errors.error("Invalid number of arguments, expects 1",
                         note=usage_note,
                         line=args.position)

        platform_arg = args.children[0]

        if not isinstance(platform_arg, stringliteral.StrLiteral):
            errors.error("Expected argument to be a string literal",
                         note=usage_note,
                         line=platform_arg.position)

        self.platform = platform_arg.value.lower()[:-1]  # remove 0x00 char

        if self.platform not in VALID_PLATFORMS:
            errors.error(f"Platform string must be in this list: [{', '.join(VALID_PLATFORMS)}]",
                         line=platform_arg.position)

    @property
    def should_compile(self):
        return platform.system().lower() == self.platform

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