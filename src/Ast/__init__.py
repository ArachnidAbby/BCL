
from typing import List, Tuple

from llvmlite import ir

from .Ast_Types import *
from .conditionals import *
from .function import *
from .loops import *
from .math import *
from .nodes import *
from .standardfunctions import *
from .variable import *


class Literal(ExpressionNode):
    __slots__ = ('value', 'ir_type')
    name = 'literal'

    def init(self, value: Any, typ: Ast_Types.AbstractType):
        self.value = value
        self.ret_type = typ

        self.ir_type = typ.ir_type

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)
