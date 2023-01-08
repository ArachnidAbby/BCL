import errors
from llvmlite import ir

from .nodes import *


class StructDef(ASTNode):
    __slots__ = ("struct_name", "block", "struct_type", "block")

    def __init__(self, pos: SrcPosition, name, block, module):
        super().__init__(pos)
        if name.value in Ast_Types.types_dict.keys():
            errors.error(f"Type name already in use: {name.value}", line = name.pos, full_line=True)

        self.struct_name = name.value
        self.block = block
        members = self.block.children[0].children
        self.struct_type = Ast_Types.Struct(self.struct_name, members, module)
        Ast_Types.types_dict[self.struct_name] = self.struct_type
        
    def pre_eval(self):
        pass

    def eval(self):
        pass
