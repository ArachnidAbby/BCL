'''This module exists to avoid circular imports, its annoying'''

from llvmlite import ir

import errors

from ..Ast_Types import Type_Base


class VariableObj:
    '''Represents a variable.'''
    __slots__ = ("ptr", "type", "is_constant", "range", "is_arg",
                 "arg_idx")

    def __init__(self, ptr, typ, is_constant, arg_idx=0):
        self.ptr = ptr
        self.type = typ
        # ? Is this still necessary
        if isinstance(typ, str):
            self.type = Type_Base.types_dict[typ]()
        self.is_constant = is_constant
        self.is_arg = is_constant
        self.arg_idx = arg_idx
        self.range = self.type.rang

    @property
    def ret_type(self):
        return self.type

    def define(self, func, name, idx):
        '''alloca memory for the variable'''
        if self.is_constant:
            return self.ptr

        if func.yields:
            self.ptr = func.builder.gep(func.yield_struct_ptr,
                                        [ir.Constant(ir.IntType(32), 0),
                                         ir.Constant(ir.IntType(32), 4),
                                         ir.Constant(ir.IntType(32), idx)])
            return self.ptr
        self.ptr = func.builder.alloca(self.type.ir_type, name=name)
        return self.ptr

    def store(self, func, value):
        if self.is_constant:
            errors.error("Variable is constant, cannot assign value",
                         line=value.poisition)

        self.type.assign(func, self, value, self.type)

    def get_value(self, func):
        if not self.is_constant:
            return func.builder.load(self.ptr)
        return self.ptr

    def get_namespace_name(self, func, name, pos):
        return self.type.get_namespace_name(func, name, pos)

    def __repr__(self) -> str:
        return f'VAR: |{self.ptr}, {self.type}, {self.is_constant}|'
