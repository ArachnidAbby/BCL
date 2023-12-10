
from llvmlite import ir

import errors
from Ast.directives.basedirective import CompilerDirective
from Ast.literals import stringliteral

usage_note = "Example: LLComment(\"This is a fun comment\")"


class LLCommentDirective(CompilerDirective):
    __slots__ = ("comment",)

    def __init__(self, pos, args, original_stmt, module):
        super().__init__(pos, args, original_stmt, module)

        if len(args) != 1:
            errors.error("Invalid number of arguments, expects 1",
                         note=usage_note,
                         line=args.position)

        comment_arg = args.children[0]

        if not isinstance(comment_arg, stringliteral.StrLiteral):
            errors.error("Expected argument to be a string literal",
                         note=usage_note,
                         line=pos)

        self.comment = comment_arg.value[:-1]  # remove 0x00 char

    def eval_impl(self, func):
        super().eval_impl(func)
        func.builder.comment(self.comment)
