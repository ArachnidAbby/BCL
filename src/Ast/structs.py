import Ast.Ast_Types as Ast_Types
import errors
from Ast.functions.definition import FunctionDef
from Ast.nodes import ASTNode, KeyValuePair
from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.container import ContainerNode


class StructDef(ASTNode):
    __slots__ = ("struct_name", "block", "struct_type", "block", "module")

    def __init__(self, pos: SrcPosition, name, block, module):
        super().__init__(pos)
        if name.value in Ast_Types.types_dict.keys():
            errors.error(f"Type name already in use: {name.value}",
                         line=name.pos, full_line=True)

        self.struct_name = name.value.var_name
        self.block = block
        if isinstance(self.block.children[0], ContainerNode):
            members = self.block.children[0].children
        elif isinstance(self.block.children[0], KeyValuePair):
            members = [self.block.children[0]]
        else:
            errors.error("The first statement in a struct definition MUST "+
                         "be a list of members", line=self.block.children[0].pos)
        self.struct_type = Ast_Types.Struct(self.struct_name, members, module)
        module.types[self.struct_name] = self.struct_type
        self.module = module

    @property
    def ir_type(self):
        return self.struct_type.ir_type

    def get_type(self, _):
        return self.struct_type

    def get_unique_name(self, name: str) -> str:
        return self.module.get_unique_name(f"__meth.{self.struct_name}.{name}")

    def _yield_functions(self):
        # skip first element
        for statement in self.block.children[1:]:
            if isinstance(statement, FunctionDef):
                yield statement
            else:
                errors.error("Struct bodies can only contain function " +
                             "declarations or member declarations",
                             line=statement.pos)

    def create_function(self, name: str, func_obj):
        self.struct_type.create_function(name, func_obj)

    def post_parse(self, module):
        self.struct_type.define(self)

        for stmt in self._yield_functions():
            # stmt.func_name = f"{stmt.func_name}"
            stmt.post_parse(self)

    def pre_eval(self, module):
        for stmt in self._yield_functions():
            stmt.pre_eval(self)

    def eval(self, module):
        for stmt in self._yield_functions():
            stmt.eval(self)

    def repr_as_tree(self) -> str:
        return self.create_tree("Struct Def Statement",
                                name=self.struct_name,
                                contents=self.block)
