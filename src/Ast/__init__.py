
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

class TypeRefLiteral(ExpressionNode):
    __slots__ = ('value')
    name = 'literal'

    def init(self, value: Any):
        self.value = value
        self.ret_type = value

        self.ir_type = value.ir_type


class ArrayLiteral(ExpressionNode):
    __slots__ = ('value', 'ir_type')
    name = 'literal'

    def init(self, value: List[Any]):
        self.value = value
        
    
    def pre_eval(self):
        self.value[0].pre_eval()
        typ = self.value[0].ret_type

        for x in self.value:
            x.pre_eval()
            if x.ret_type!=typ:
                errors.error(f"Invalid type '{x.ret_type}' in a list of type '{typ}'", line = x.position)
            

        array_size  = Literal((-1,-1,-1), len(self.value), Ast_Types.Integer_32)
        self.ret_type = Ast_Types.Array(array_size, typ, None)
        self.ir_type = self.ret_type.ir_type

    def eval(self, func) -> ir.Constant:
        # l = []
        # for x in self.value:
        #     l.append(x.eval())

        return ir.Constant.literal_array([x.eval(func) for x in self.value])
