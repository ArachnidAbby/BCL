from typing import Any

import errors
from llvmlite import ir

from Ast import Ast_Types
from Ast.nodes import ExpressionNode


class Literal(ExpressionNode):
    __slots__ = ('value', 'ir_type')
    name = 'literal'

    def init(self, value: Any, typ: Ast_Types.Type):
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
    
    def eval(self, func):
        #print(self.value, Ast_Types.types_dict)
        if isinstance(self.value, str):
            self.value = Ast_Types.types_dict[self.value]()
            self.ret_type = self.value
            self.ir_type = self.value.ir_type
        else:
            self.ret_type = self.value
            self.ir_type = self.value.ir_type


class ArrayLiteral(ExpressionNode):
    __slots__ = ('value', 'ir_type')
    name = 'literal'

    def init(self, value: list[Any]):
        self.value = value
        self.position = list(self.merge_pos(tuple([x.position for x in self.value])))
        self.position[2] += 1
        self.position = tuple(self.position)
        
    def pre_eval(self):
        self.value[0].pre_eval()
        typ = self.value[0].ret_type

        for x in self.value:
            x.pre_eval()
            if x.ret_type!=typ:
                errors.error(f"Invalid type '{x.ret_type}' in a list of type '{typ}'", line = x.position)
            

        array_size  = Literal((-1,-1,-1), len(self.value), Ast_Types.Integer_32)
        self.ret_type = Ast_Types.Array(array_size, typ)
        self.ir_type = self.ret_type.ir_type

    def eval(self, func) -> ir.Constant:
        return ir.Constant.literal_array([x.eval(func) for x in self.value])
