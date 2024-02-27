
import errors
from Ast.directives.basedirective import CompilerDirective

usage_note = f"""Example:
{errors.RED}|   {errors.RESET}#[WrapperType]
{errors.RED}|   {errors.RESET}struct %s"""


class WrapperDirective(CompilerDirective):
    __slots__ = ()

    def __init__(self, pos, args, original_stmt, module):
        super().__init__(pos, args, original_stmt, module)
        from Ast.structs import StructDef

        if not isinstance(original_stmt, StructDef):
            errors.error("Directive only works on struct definitions",
                         note=usage_note % ("my_function"),
                         line=args.position)

        if len(args) != 0:
            errors.error("Directive takes no arguments",
                         note=usage_note % (original_stmt.struct_name),
                         line=args.position)

        original_stmt.is_wrapper = True
