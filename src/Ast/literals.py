from typing import Any

import errors
from llvmlite import ir

from Ast import Ast_Types
from Ast.nodes import ExpressionNode


class Literal(ExpressionNode):
    __slots__ = ('value', 'ir_type', 'ptr')
    name = 'literal'

    def init(self, value: Any, typ: Ast_Types.Type):
        self.value = value
        self.ret_type = typ

        self.ir_type = typ.ir_type

    def eval(self, func) -> ir.Constant:
        return ir.Constant(self.ir_type, self.value)
    
    def __str__(self) -> str:
        return str(self.value)

class TypeRefLiteral(ExpressionNode):
    __slots__ = ('value')
    name = 'literal'

    def init(self, value: Any):
        self.value = value
        self.ret_type = value
    
    def eval(self, func):
        #print(self.value, Ast_Types.types_dict)
        if isinstance(self.value, str):
            if self.value not in Ast_Types.types_dict.keys():
                errors.error(f"Undeclared type: '{self.value}'", line = self.position)
            self.value = Ast_Types.types_dict[self.value]()
            self.ret_type = self.value
            self.ir_type = self.value.ir_type
        else:
            self.ret_type = self.value
            self.ir_type = self.value.ir_type

class ArrayLiteral(ExpressionNode):
    __slots__ = ('value', 'ir_type', 'literal')
    name = 'literal'

    def init(self, value: list[Any]):
        self.value = value
        self.ptr = None
        self.literal = True # whether or not this array is only full of literals
        
    def pre_eval(self, func):
        self.value[0].pre_eval(func)
        typ = self.value[0].ret_type

        for x in self.value:
            x.pre_eval(func)
            if x.ret_type!=typ:
                errors.error(f"Invalid type '{x.ret_type}' in a list of type '{typ}'", line = x.position)
            if x.name!='literal':
                self.literal = False
            

        array_size  = Literal((-1,-1,-1), len(self.value), Ast_Types.Integer_32)
        self.ret_type = Ast_Types.Array(array_size, typ)
        self.ir_type = self.ret_type.ir_type

    def eval(self, func):
        if not self.literal:
            ptr = func.create_const_var(self.ret_type)
            zero_const = ir.Constant(ir.IntType(64), 0)
            for c, item in enumerate(self.value):
                index = ir.Constant(ir.IntType(32), c)
                item_ptr = func.builder.gep(ptr , [zero_const, index])
                func.builder.store(item.eval(func), item_ptr)
            self.ptr = ptr
            return func.builder.load(ptr)
        
        return ir.Constant.literal_array([x.eval(func) for x in self.value])
    
    @property
    def position(self) -> tuple[int, int, int]:
        x = list(self.merge_pos([x.position for x in self.value]))  # type: ignore
        x[2] += 1
        return tuple(x)


class StrLiteral(ExpressionNode):
    __slots__ = ('value', 'ir_type')
    name = 'literal'

    def init(self, value: str):
        self.value = value
        
    def pre_eval(self, func):
        array_size  = Literal((-1,-1,-1), len(self.value), Ast_Types.Integer_32)
        self.ret_type = Ast_Types.StringLiteral(array_size)
        self.ir_type = self.ret_type.ir_type

    def eval(self, func) -> ir.Constant:
        const = ir.Constant(ir.ArrayType(ir.IntType(8), len(self.value.encode("utf-8"))),
        bytearray(self.value.encode("utf-8")))
        ptr = func.builder.alloca(ir.ArrayType(ir.IntType(8), len(self.value.encode("utf-8"))))
        func.builder.store(const, ptr)
        return ptr
    
    def get_ptr(self, func):
        return func.builder.bitcast(self.eval(func), ir.IntType(8).as_pointer())

class RangeLiteral(ExpressionNode):
    __slots__ = ('start', 'end')
    name = 'literal'

    def init(self, start: Any, end: Any):
        self.start = start
        self.end = end
    
    def pre_eval(self, func):
        self.start.pre_eval(func)
        self.end.pre_eval(func)

    def eval(self, func):
        self.start = self.start.eval(func)
        self.end = self.end.eval(func)

    @property
    def position(self) -> tuple[int, int, int]:
        return self.merge_pos((self.start.position, self.end.position))
