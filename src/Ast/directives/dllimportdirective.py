import errors
from Ast.directives.basedirective import CompilerDirective

usage_code_example = errors.highlight_code("""#[DLLImport]
define my_dllimport();""")

usage_note = f"Example: \n{errors.RESET}{usage_code_example}"


class DLLImportDirective(CompilerDirective):
    __slots__ = ("directive_arg")

    def __init__(self, pos, args, original_stmt, module):
        super().__init__(pos, args, original_stmt, module)

        if len(args) != 0:
            errors.error("Directive takes no arguments",
                         note=usage_note,
                         line=args.position)

        from Ast.functions.definition import FunctionDef

        if not isinstance(original_stmt, FunctionDef):
            errors.error("Directive only works on function definitions",
                         note=usage_note,
                         line=args.position)

    def post_parse(self, func):
        super().post_parse(func)
        self.original_stmt.function_ir.linkage += "dllimport"
