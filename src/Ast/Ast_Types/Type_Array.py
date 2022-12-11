from Ast.Ast_Types import Type_I32
from Ast.nodetypes import NodeTypes
from errors import error, inline_warning
from llvmlite import ir

from . import Type_Base


class Array(Type_Base.Type):
    __slots__ = ('size', 'typ')
    name = "array"
    pass_as_ptr = True
    no_load = False

    def __init__(self, size, typ):
        self.typ = typ
        if typ.name == "literal":
            typ.eval(None)
            self.typ = typ.value # elements' type

        if size.name != "literal":
            error(f"size of array type must be a int-literal", line = size.position)\
        
        self.size = size.value
        
        if self.size <= 0:
            error(f"Array size must be > 0", line = size.position)
        elif size.ret_type != Type_I32.Integer_32:
            error(f"Array size must be an integer", line = size.position)

        typ.eval(None)
        self.ir_type = ir.ArrayType(typ.ir_type, self.size)

    @staticmethod
    def convert_from(func, typ: str, previous):
        error(f"type '{typ}' cannot be converted to type 'Array<{typ}>'", line = previous.position)

    def convert_to(self, func, orig, typ):
        if typ!=self:
            error(f"Cannot convert 'Array<{orig.ir_type.element}>' to type '{typ}'", line = orig.position)
        return orig.eval(func)
    
    def get_op_return(self, op, lhs, rhs):
        if op == "ind":
            return self.typ

    def __eq__(self, other):
        if (other == None) or other.name != self.name:
            return False
        
        return other.typ == self.typ and other.size == self.size

    def __neq__(self, other):
        if (other == None) or other.name != self.name:
            return True
        
        return other.typ != self.typ or other.size != self.size

    def __hash__(self):
        return hash(f"{self.name}--|{self.size}|")

    def index(self, func, lhs):
        return func.builder.load(lhs.get_ptr(func))
    
    def put(self, func, lhs, value):
        return func.builder.store(value.eval(func), lhs.get_ptr(func))

    def __repr__(self) -> str:
        return f"{self.typ}[{self.size}]"
    
    def __str__(self) -> str:
        return f"{self.typ}[{self.size}]"
