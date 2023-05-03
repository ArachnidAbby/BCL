
from typing import Self

from llvmlite import ir  # type: ignore

from errors import error

# TODO: Should this be an Enum for operation names?

class Type:
    '''abstract type class that outlines the necessary
    features of a type class.'''

    __slots__ = ()
    ir_type: ir.Type = None
    name = "UNKNOWN"
    pass_as_ptr = False
    # Used for optimizations in array indexing.
    rang: tuple[int, int] | None = None
    # when allocating arguments as local vars on the stack this is checked
    # -- False: Do allocated and load, True: Don't
    no_load = False
    # useful for things like function types.
    read_only = False
    has_members = False
    # is this type allowed to be the return type of a function
    returnable = True
    # Dynamic types change function definitions and the
    # matching of function args when calling
    is_dynamic = False
    functions: dict = {"NONSTATIC": []}

    # mainly used for the function type, but makes writing other code easier
    # when included for all types
    is_method = False

    def __init__(self):
        pass

    @classmethod
    def convert_from(cls, func, typ, previous) -> ir.Instruction:
        error("Type has no conversions",  line=previous.position)

    def convert_to(self, func, orig, typ) -> ir.Instruction:
        error("Type has no conversions",  line=orig.position)

    def is_void(self) -> bool:
        return False

    def get_member(self, func, lhs,
                   name) -> tuple[ir.Instruction, Self] | None:
        return None

    def __eq__(self, other):
        return (other is not None) and self.name == other.name

    def __neq__(self, other):
        return other is None or self.name != other.name

    def get_op_return(self, op, lhs, rhs):
        pass

    def sum(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '+' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def sub(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '-' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def mul(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '*' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def div(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '/' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def mod(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '%' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def pow(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '**' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def eq(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '==' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def neq(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '!=' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def geq(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '>=' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def leq(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '<=' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def le(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '<=' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def gr(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '<=' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def _and(self, func, lhs, rhs):
        return func.builder.and_(lhs.ret_type.truthy(func, lhs),
                                 rhs.ret_type.truthy(func, rhs))

    def _or(self, func, lhs, rhs):
        return func.builder.or_(lhs.ret_type.truthy(func, lhs),
                                rhs.ret_type.truthy(func, rhs))

    def _not(self, func, rhs):
        return func.builder.not_(rhs.ret_type.truthy(func, rhs))

    def index(self, func, lhs) -> ir.Instruction:
        error(f"Operation 'index' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def put(self, func, lhs, value):
        error(f"Operation 'putat' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def call(self, func, lhs, args) -> ir.Instruction:
        error(f"type '{lhs.ret_type}' is not Callable", line=lhs.position)

    def assign(self, func, ptr, value, typ: Self):
        if self.read_only:
            error(f"Type: \'{ptr.ret_type}\' is read_only",
                  line=ptr.position)
        val = value.ret_type.convert_to(func, value, typ)  # type: ignore
        func.builder.store(val, ptr.get_ptr(func))

    def isum(self, func, ptr, rhs):
        final_value = self.sum(func, ptr, rhs)
        ptr = ptr.get_ptr(func)
        func.builder.store(final_value, ptr)

    def isub(self, func, ptr, rhs):
        final_value = self.sub(func, ptr, rhs)
        ptr = ptr.get_ptr(func)
        func.builder.store(final_value, ptr)

    def imul(self, func, ptr, rhs):
        final_value = self.mul(func, ptr, rhs)
        ptr = ptr.get_ptr(func)
        func.builder.store(final_value, ptr)

    def idiv(self, func, ptr, rhs):
        final_value = self.div(func, ptr, rhs)
        ptr = ptr.get_ptr(func)
        func.builder.store(final_value, ptr)

    def cleanup(self, func, ptr): # TODO: IMPLEMENT
        '''code to run on the closing of a function'''
        print("cleanup")

    def __hash__(self):
        return hash(self.name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}>'

    def __str__(self) -> str:
        return self.name

    def __call__(self) -> Self:
        return self

    def eval(self, foo):  # ? Why is this here
        '''Does nothing'''
        pass

    def declare(self, mod):
        '''re-declare an ir-type in a module'''

    def as_type_reference(self, func):
        return self

    def get_member_info(self, lhs, rhs):
        '''Used to get information about members
        ex: ret_type, mutability, etc
        '''

    def get_members(self):
        '''Gets all the member names.
           Must check `typ.has_members` or an Exception will occur
        '''
        return self.members.keys()  # members should always be a dict!

    def roughly_equals(self, other):
        '''check if two types are equivalent.
        This is helpful when you have compound types such as "Any"
        or a Protocol type.

        defaults to `__eq__` behavior
        '''
        return self == other

    # ? should this error instead?
    def truthy(self, func, val):
        '''When using boolean ops or if statements'''
        return ir.Constant(ir.IntType(1), 0)  # defaults false

    @property
    def ret_type(self):
        return self