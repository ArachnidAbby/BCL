import Ast.Ast_Types as Ast_Types
import errors
from Ast.nodes import ASTNode
from Ast.nodes.commontypes import SrcPosition


class StructDef(ASTNode):
    __slots__ = ("struct_name", "block", "struct_type", "block", "module")

    def __init__(self, pos: SrcPosition, name, block, module):
        super().__init__(pos)
        if name.value in Ast_Types.types_dict.keys():
            errors.error(f"Type name already in use: {name.value}",
                         line=name.pos, full_line=True)

        self.struct_name = name.value.var_name
        self.block = block
        members = self.block.children[0].children
        self.struct_type = Ast_Types.Struct(self.struct_name, members, module)
        module.types[self.struct_name] = self.struct_type
        self.module = module

    def pre_eval(self):
        self.struct_type.define(self)

    def eval(self):
        pass
