import errors
from Ast.directives.basedirective import CompilerDirective

usage_note = f"""Example:
{errors.RED}|   {errors.RESET}#[NoMangle]
{errors.RED}|   {errors.RESET}define %s();"""


class NoMangleDirective(CompilerDirective):
    __slots__ = ("directive_arg")

    def __init__(self, pos, args, original_stmt, module):
        super().__init__(pos, args, original_stmt, module)
        from Ast.functions.definition import FunctionDef

        if not isinstance(original_stmt, FunctionDef):
            errors.error("Directive only works on function definitions",
                         note=usage_note% ("my_function"),
                         line=args.position)

        if len(args) != 0:
            errors.error("Directive takes no arguments",
                         note=usage_note % (original_stmt.func_name),
                         line=args.position)


        original_stmt.use_literal_name = True
