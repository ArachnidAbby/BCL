from llvmlite import ir

from .Nodes import AST_NODE


class Integer_32(AST_NODE):
    '''The standard Integer_32 type implementation that also acts as all other `expr` nodes do.'''
    __slots__ = ["value"]

    ir_type = ir.IntType(32)

    def init(self, value):
        self.value = value
        self.name = "I32"
        self.type = "Literal"

    def eval(self, func):
        return ir.Constant(self.ir_type, self.value)
