from enum import Enum

from Ast.nodes import ASTNode, ExpressionNode
from errors import error


# todo: look into interfaces and see if this is applicable here.
class AbstractType:
    '''abstract type class that outlines the necessary features of a type class.'''

    __slots__ = ('ir_type')
    name = "UNKNOWN"

    def __init__(self):
        pass

    @classmethod
    def convert_from(cls, func, typ, previous): error(f"AbstractType has no conversions",  line = previous.position)
    
    def convert_to(self, func, orig, typ): error(f"AbstractType has no conversions",  line = orig.position)

    def is_void(self) -> bool:
        return self.name == "void"

    def __eq__(self, other):
        return (other is not None) and self.name == other.name
    def __neq__(self, other):
        return other is None or self.name != other.name

    # todo: remove this
    @classmethod
    def print_error(cls, op: str, lhs, rhs):
        if op=='not': cls._not(None, None, rhs)

        {
            'sum': cls.sum,
            'sub': cls.sub,
            'mul': cls.mul,
            'div': cls.div,
            'mod': cls.mod,
            'eq': cls.eq,
            'neq': cls.neq,
            'geq': cls.geq,
            'leq': cls.leq,
            'le': cls.le,
            'gr': cls.gr,
            'and': cls._and,
            'or': cls._or,
        }[op](None, None, lhs, rhs)

    
    def get_op_return(self, op, lhs, rhs): pass


    
    def sum  (self, func, lhs, rhs): error(f"Operator '+' is not supported for type '{lhs.ret_type}'",  line = lhs.position)
    
    def sub  (self, func, lhs, rhs): error(f"Operator '-' is not supported for type '{lhs.ret_type}'",  line = lhs.position)
    
    def mul  (self, func, lhs, rhs): error(f"Operator '*' is not supported for type '{lhs.ret_type}'",  line = lhs.position)
    
    def div  (self, func, lhs, rhs): error(f"Operator '/' is not supported for type '{lhs.ret_type}'",  line = lhs.position)
    
    def mod  (self, func, lhs, rhs): error(f"Operator '%' is not supported for type '{lhs.ret_type}'",  line = lhs.position)

    
    def eq   (self, func, lhs, rhs): error(f"Operator '==' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    def neq  (self, func, lhs, rhs): error(f"Operator '!=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    def geq  (self, func, lhs, rhs): error(f"Operator '>=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    def leq  (self, func, lhs, rhs): error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    def le   (self, func, lhs, rhs): error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    def gr   (self, func, lhs, rhs): error(f"Operator '<=' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    
    def _not (self, func, rhs): error(f"Operator 'not' is not supported for type '{rhs.ret_type}'",line = rhs.position)
    
    def _and (self, func, lhs, rhs): error(f"Operator 'and' is not supported for type '{lhs.ret_type}'",line = lhs.position)
    
    def _or  (self, func, lhs, rhs): error(f"Operator 'or' is not supported for type '{lhs.ret_type}'", line = lhs.position)

    
    def index  (self, func, lhs, rhs): error(f"Operation 'index' is not supported for type '{lhs.ret_type}'", line = lhs.position)
    
    def __hash__(self):
        return hash(self.name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}>'
    
    def __str__(self) -> str:
        return self.name



from .Type_Bool import Integer_1
from .Type_F32 import Float_32
from .Type_I32 import Integer_32
from .Type_Void import Void

types_dict = {
    'void': Void,
    'bool': Integer_1,
    "i32": Integer_32,
    "int": Integer_32,
    'f32': Float_32,
    'float': Float_32
}

# todo: replace strings in the future
conversion_priority_raw = [
    AbstractType(),
    Integer_1(),
    Integer_32(),
    'i64',
    Float_32(),
    'f64'
] # the further down the list this is, the higher priority

def get_std_ret_type(self: ExpressionNode,  other: ExpressionNode):
    '''When a math operation happens between types, we need to know what the final return type will be.'''
    conversion_priority = {x: c for c,x in enumerate(conversion_priority_raw)}
    largest_priority = max(
        conversion_priority[self.ret_type],
        conversion_priority[other.ret_type]
    )

    return conversion_priority_raw[largest_priority]
