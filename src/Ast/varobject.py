'''This module exists to avoid circular imports, its annoying'''

from .Ast_Types import Type_Base


class VariableObj:
    '''allows variables to be stored on the heap. This lets me pass them around by reference.'''
    __slots__ = ("ptr", "type", "is_constant", "range")

    def __init__(self, ptr, typ, is_constant):
        self.ptr = ptr
        self.type = typ
        if isinstance(typ, str):
            self.type = Type_Base.types_dict[typ]()
        self.is_constant = is_constant
        self.range = self.type.rang

    @property
    def ret_type(self):
        return self.type
    
    def define(self, func, name):
        '''alloca memory for the variable'''
        if self.is_constant:
            return self.ptr
        ptr = func.builder.alloca(self.type.ir_type, name=name)
        self.ptr = ptr
        return ptr
    
    def store(self, func, value):
        self.type.assign(func, self, value, self.type)
        # func.builder.store(value.eval(func), self.ptr)
    
    def get_value(self, func):
        if not self.is_constant: 
            return func.builder.load(self.ptr) 
        return self.ptr
        

    def __repr__(self) -> str:
        return f'VAR: |{self.ptr}, {self.type}, {self.is_constant}|'
