from llvmlite import ir

from .Nodes import *
from . import Types

class Sum(AST_NODE):
    def init(self):
        self.ir_type = Types.Number.ir_type
        for x in self.children:
            if x.type == 'literal' and x.name=='f32':
                return None

    def eval(self, func):
        return func.builder.add(self.children[0].eval(func), self.children[1].eval(func))

class Sub(AST_NODE):
    def init(self):
        self.ir_type = Types.Number.ir_type
        for x in self.children:
            if x.type == 'literal' and x.name=='f32':
                return None

    def eval(self, func):
        return func.builder.sub(self.children[0].eval(func), self.children[1].eval(func))