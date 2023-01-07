from llvmlite import ir

from .nodes import *


class StructDef(ASTNode):
    def __init__(self, pos: SrcPosition, name, block):
        super().__init__(pos)
