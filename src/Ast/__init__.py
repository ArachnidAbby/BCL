
from typing import List, Tuple

from llvmlite import ir

from .Ast_Types import *
from .Conditionals import *
from .Function import *
from .Loops import *
from .Math import *
from .Nodes import *
from .Standard_Functions import *
from .Variable import *


class Literal(ExpressionNode):
    __slots__ = ('value', 'ir_type')

    def init(self, value: Any, typ: Ast_Types.AbstractType):
        self.value = value
        self.name = 'literal'
        self.ret_type = typ

        self.ir_type = typ.ir_type

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)
