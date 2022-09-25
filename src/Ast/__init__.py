
from typing import List, Tuple

from llvmlite import ir

from .Conditionals import *
from .Loops import *
from .Function import *
from .Math import *
from .Nodes import *
from .Standard_Functions import *
from .Ast_Types import *
from .Variable import *

class Literal(AST_NODE):
    __slots__ = ('value', 'ir_type')

    def init(self, value: Any, typ: Ast_Types.AbstractType):
        self.value = value
        self.name = 'literal'
        self.type = NodeTypes.EXPRESSION
        self.ret_type = typ

        self.ir_type = typ.ir_type

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)