
from typing import Self

from llvmlite import ir

from Ast.nodes.commontypes import Modifiers
from Ast.nodes.passthrough import PassNode  # type: ignore
from errors import error


class Type:
    '''abstract type class that outlines the necessary
    features of a type class.'''

    __slots__ = ()
    ir_type: ir.Type = None
    name = "UNKNOWN/UNQUALIFIED"
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
    checks_lifetime = False
    # Dynamic types change function definitions and the
    # matching of function args when calling
    is_dynamic = False
    # ? should this be here still?
    functions: dict = {"NONSTATIC": []}
    # Is this type iterable, or does iterating return a new iterator?
    is_iterator = False

    # mainly used for the function type, but makes writing other code easier
    # when included for all types
    is_method = False

    # Only allow indexes via literals
    literal_index = False

    # Namespacing stuff that applies to nodes also applies to types
    is_namespace = True
    needs_dispose = False
    is_generic = False
    ref_counted = False
    visibility = Modifiers.VISIBILITY_PUBLIC
    generate_bounds_check = True
    index_returns_ptr = True

    def __init__(self):
        pass

    def global_namespace_names(self, func, name, pos):
        from Ast.Ast_Types.Type_I32 import Integer_32
        from Ast.literals.numberliteral import Literal
        if name == "SIZEOF":
            target_data = func.module.target_machine.target_data
            size = self.ir_type.get_abi_size(target_data)
            ty = Integer_32(name="u64", size=64, signed=False)
            val = Literal(pos, size, ty)
            return val

    def get_namespace_name(self, func, name, pos):
        '''Getting a name from the namespace'''
        if x := self.global_namespace_names(func, name, pos):
            return x
        error(f"Cannot get {name} from namespace {self}", line=pos)

    def pass_type_params(self, func, params, pos):
        error(f"Type is not Generic: {self}", line=pos)

    @classmethod
    def convert_from(cls, func, typ, previous) -> ir.Instruction:
        if previous.ret_type == typ:
            return previous.eval(func)
        error("Type has no conversions",  line=previous.position)

    def convert_to(self, func, orig, typ) -> ir.Instruction:
        if orig.ret_type == typ:
            return orig.eval(func)
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

    def _simple_call_op_error_check(self, op, lhs, rhs):
        '''Error check for non-callable types'''
        if op == "call" and rhs.position.line > lhs.position.line:
            error(f"{self} is not callable, perhaps you forgot a semicolon?",
                  line=lhs.position)
        elif op == "call":
            error(f"{self} is not callable",
                  line=lhs.position)

    def get_op_return(self, func, op, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
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

    def lshift(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '<<' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def rshift(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '>>' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def bit_xor(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '^' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def bit_not(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '~' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def bit_or(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '|' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def bit_and(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operator '&' is not supported for type '{lhs.ret_type}'",
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

    def index(self, func, lhs, rhs) -> ir.Instruction:
        error(f"Operation 'index' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def put(self, func, lhs, value):
        error(f"Operation 'put at index' is not supported for type '{lhs.ret_type}'",
              line=lhs.position)

    def call(self, func, lhs, args) -> ir.Instruction:
        error(f"type '{lhs.ret_type}' is not Callable", line=lhs.position)

    def get_assign_type(self, func, value):
        return self

    def assign(self, func, ptr, value, typ: Self, first_assignment=False):
        if self.read_only and not first_assignment:
            error(f"Type: \'{ptr.ret_type}\' is read_only",
                  line=ptr.position)

        val = value.ret_type.convert_to(func, value, typ)  # type: ignore

        node = PassNode(value.position, val, typ)

        value.ret_type.add_ref_count(func, node)

        func.builder.store(val, ptr.get_ptr(func))

    def isum(self, func, ptr, rhs):
        val = func.builder.load(ptr.get_ptr(func))
        node = PassNode(ptr.position, val, self, ptr.get_ptr(func))

        sum_value = self.sum(func, node, rhs)
        sum_node = PassNode(rhs.position, sum_value, self.get_op_return(func, 'sum', ptr, rhs))
        # final_value = sum_node.ret_type.convert_to(func, sum_node, ptr.ret_type)

        # ptr = ptr.get_ptr(func)
        # func.builder.store(final_value, ptr)
        ptr.store(func, ptr, sum_node, self)

    def isub(self, func, ptr, rhs):
        val = func.builder.load(ptr.get_ptr(func))
        node = PassNode(ptr.position, val, self, ptr.get_ptr(func))

        sub_value = self.sub(func, node, rhs)
        sub_node = PassNode(rhs.position, sub_value, self.get_op_return(func, 'sub', ptr, rhs))
        # final_value = sub_node.ret_type.convert_to(func, sub_node, ptr.ret_type)

        # ptr = ptr.get_ptr(func)
        # func.builder.store(final_value, ptr)
        ptr.store(func, ptr, sub_node, self)

    def imul(self, func, ptr, rhs):
        val = func.builder.load(ptr.get_ptr(func))
        node = PassNode(ptr.position, val, self, ptr.get_ptr(func))

        mul_value = self.mul(func, node, rhs)
        mul_node = PassNode(rhs.position, mul_value, self.get_op_return(func, 'mul', ptr, rhs))
        # final_value = mul_node.ret_type.convert_to(func, mul_node, ptr.ret_type)

        # ptr = ptr.get_ptr(func)
        # func.builder.store(final_value, ptr)
        ptr.store(func, ptr, mul_node, self)

    def idiv(self, func, ptr, rhs):
        val = func.builder.load(ptr.get_ptr(func))
        node = PassNode(ptr.position, val, self, ptr.get_ptr(func))

        div_value = self.div(func, node, rhs)
        div_node = PassNode(rhs.position, div_value, self.get_op_return(func, 'div', ptr, rhs))
        # final_value = div_node.ret_type.convert_to(func, div_node, ptr.ret_type)

        # ptr = ptr.get_ptr(func)
        # func.builder.store(final_value, ptr)
        ptr.store(func, ptr, div_node, self)

    def __hash__(self):
        return hash(self.name)

    def __repr__(self) -> str:
        return f'<Type: {self.name}>'

    def __str__(self) -> str:
        return self.name

    def __call__(self) -> Self:
        return self

    def eval_impl(self, foo):  # ? Why is this here
        '''Does nothing'''
        pass

    def declare(self, mod):
        '''re-declare an ir-type in a module'''

    def as_type_reference(self, func, allow_generics=False):
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
    def type(self):
        return self

    @property
    def ret_type(self):
        return self

    def get_iter_return(self, loc):
        error(f"{self.name} is not Iterable", line=loc)

    def create_iterator(self, func, loc):
        '''should return a ptr'''
        if not self.is_iterator:
            error(f"{self.name} is not Iterable", line=loc)  # default
        else:
            error(f"{self.name} is already an Iterator", line=loc)

    def iter_condition(self, func, self_ptr, loc):
        error(f"{self.name} is not Iterable", line=loc)

    def iter(self, func, self_ptr, loc):
        error(f"{self.name} is not Iterable", line=loc)

    def iter_get_val(self, func, self_ptr, loc):
        error(f"{self.name} is not Iterable", line=loc)

    def pass_to(self, func, item):
        if self.pass_as_ptr:
            return item.get_ptr(func)
        return item.eval(func)

    # TODO: Document this better
    # or change code
    def recieve(self, func, item):
        if self.pass_as_ptr:
            val = func.builder.load(item[0].ptr)
        else:
            val = item[0].ptr

        ptr = func.builder.alloca(item[0].type.ir_type)
        func.builder.store(val, ptr)
        item[0].ptr = ptr

    def add_ref_count(self, func, ptr):
        # print(f"add_ref_count {func.func_name} {self}")
        pass

    def pop_ref_count(self, func, ptr):
        pass

    def dispose(self, func, ptr):
        '''code to run on the closing of a function'''
        self.pop_ref_count(func, ptr)
        # print(f"dispose {func.func_name} {self}")

    def get_deref_return(self, func, node):
        error(f"Cannot dereference type, {self}", line=node.position)

    def deref(self, func, node):
        error(f"Cannot dereference type, {self}", line=node.position)
