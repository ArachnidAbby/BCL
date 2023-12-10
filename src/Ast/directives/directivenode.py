
import errors
from Ast.directives.anddirective import AndDirective
from Ast.directives.llcommentdirective import LLCommentDirective
from Ast.directives.notdirective import NotDirective
from Ast.directives.ordirective import OrDirective
from Ast.directives.platformdirective import PlatformDirective
from Ast.functions.call import FunctionCall
from Ast.nodes.astnode import ASTNode
from Ast.nodes.parenthese import ParenthBlock
from Ast.variables.reference import VariableRef

# All known compiler directives, given names
directives = {
    "Platform": PlatformDirective,
    "LLComment": LLCommentDirective,
    "Not": NotDirective,
    "Or": OrDirective,
    "And": AndDirective
}


def names_to_directives(directives_raw: list[FunctionCall | VariableRef],
                        module, orginal_stmt):
    output = []

    for directive_raw in directives_raw:
        if not (isinstance(directive_raw, FunctionCall) or isinstance(directive_raw, VariableRef)):
            errors.error("Invalid compiler directive. Must be a name or function call.",
                         line=directive_raw.position)

        if isinstance(directive_raw, FunctionCall):
            if not isinstance(directive_raw.func_name, VariableRef):
                errors.error("Function name must be a variable-style name",
                             line=directive_raw.func_name.position)
            directive_name = directive_raw.func_name.var_name
            directive_name_pos = directive_raw.func_name.position
            args = directive_raw.paren
        else:
            directive_name = directive_raw.var_name
            directive_name_pos = directive_raw.position
            args = ParenthBlock(directive_name_pos)

        if directive_name not in directives.keys():
            errors.error("Directive with that name is not found",
                         line=directive_name_pos)

        directive_class = directives[directive_name]

        output.append(
            directive_class(directive_name_pos, args, orginal_stmt, module)
        )

    return output


class DirectiveList(ASTNode):
    __slots__ = ("directives", "statement", "raw_directives", "module")

    def __init__(self, pos,
                 module,
                 statement,
                 directives: list[FunctionCall | VariableRef]):
        super().__init__(pos)

        self.raw_directives = directives
        self.directives = names_to_directives(directives, module, statement)
        self.statement = statement
        self.module = module

        prev_stmt = self.statement
        for directive in self.directives:
            directive.original_stmt = self.statement
            directive.passed_stmt = prev_stmt

        from Ast import enumdef
        from Ast.structs import StructDef

        if not self.should_compile:
            module.remove_scheduled(statement)

            if isinstance(statement, StructDef):
                del module.types[statement.struct_name]
            if isinstance(statement, enumdef.Definition):
                del module.types[statement.enum_name]

    @property
    def should_compile(self):
        return all((directive.should_compile for directive in self.directives))

    def copy(self, original_stmt=None):
        return DirectiveList(self._position,
                             self.module,
                             self.statement.copy(),
                             self.raw_directives)

    def reset(self):
        self.directives[-1].reset()

    def fullfill_templates(self, func):
        if not self.should_compile:
            return
        self.directives[-1].fullfill_templates(func)

    def post_parse(self, func):
        if not self.should_compile:
            return
        self.directives[-1].post_parse(func)

    def pre_eval(self, func):
        if not self.should_compile:
            return
        self.directives[-1].pre_eval(func)

    def eval_impl(self, func):
        if not self.should_compile:
            return
        self.directives[-1].eval_impl(func)

    # def get_position(self):
    #     return self.statement.get_position()
