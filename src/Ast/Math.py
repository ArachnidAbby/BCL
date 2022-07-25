from llvmlite import ir

from . import Types
from .Nodes import *


class Sum(AST_NODE):
    '''Basic sum operation. It acts as an `expr`'''
    __slots__ = ["ir_type"]

    def init(self):
        self.ir_type = Types.Integer_32.ir_type
        for x in self.children:
            if x.type == 'literal' and x.name=='f32':
                return None

    def eval(self, func):
        return func.builder.add(self.children[0].eval(func), self.children[1].eval(func))

class Sub(AST_NODE):
    '''Basic sum operation. It acts as an `expr`'''
    __slots__ = ["ir_type"]
    
    def init(self):
        self.ir_type = Types.Integer_32.ir_type
        for x in self.children:
            if x.type == 'literal' and x.name=='f32':
                return None

    def eval(self, func):
        return func.builder.sub(self.children[0].eval(func), self.children[1].eval(func))
