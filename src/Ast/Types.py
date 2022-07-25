from llvmlite import ir

from .Nodes import AST_NODE


class Number(AST_NODE):
    ir_type = ir.IntType(32)
    def init(self, value):
        self.value = value
        self.name = "I32"
        self.type = "Literal"

    def eval(self, func):
        return ir.Constant(self.ir_type, self.value)
