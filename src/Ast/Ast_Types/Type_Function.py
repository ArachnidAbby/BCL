from typing import Self

from llvmlite import ir  # type: ignore

from Ast import Ast_Types
from Ast.functions.functionobject import _Function
from errors import error


class Function(Ast_Types.Type):
    '''abstract type class that outlines the necessary features
    of a type class.'''

    __slots__ = ('func_name', 'module', 'versions')
    name = "FUNCTION"
    pass_as_ptr = False
    no_load = False
    read_only = True

    # TODO: implement struct methods
    def __init__(self, name: str, module):
        self.func_name = name
        self.module = module
        self.versions: dict[tuple, _Function] = {}
        module.globals[name] = self

    def create(self, args: tuple, func_ir):
        '''create a function with that name'''
        self.versions[args] = func_ir

    # TODO: allow casting overloads
    @classmethod
    def convert_from(cls, func, typ, previous) -> ir.Instruction:
        error("Function type has no conversions",  line=previous.position)

    def convert_to(self, func, orig, typ) -> ir.Instruction:
        error("Function type has no conversions",  line=orig.position)

    def __eq__(self, other):
        return super().__eq__(other) and \
            other.func_name == self.func_name

    def __neq__(self, other):
        return super().__neq__(other) and \
            other.func_name != self.func_name

    # TODO: implement this
    def get_op_return(self, op, lhs, rhs):
        if op == "call":
            pass

    def __hash__(self):
        return hash(self.name+self.struct_name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}--{self.func_name}>'

    def __str__(self) -> str:
        return self.func_name

    def __call__(self) -> Self:
        return self
