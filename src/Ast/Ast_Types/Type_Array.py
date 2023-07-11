from llvmlite import ir  # type: ignore

from Ast.Ast_Types import Type_I32
from Ast.nodes.commontypes import MemberInfo
from Ast.nodes.passthrough import PassNode
from errors import error

from . import Type_Base


class Array(Type_Base.Type):
    __slots__ = ('size', 'typ', 'ir_type', 'needs_dispose', 'ref_counted')
    name = "array"
    pass_as_ptr = True
    no_load = False
    has_members = True

    def __init__(self, size, typ):
        self.typ = typ
        self.needs_dispose = typ.needs_dispose
        self.ref_counted = typ.ref_counted

        if not size.isconstant:
            error("size of array type must be a int-literal",
                  line=size.position)

        self.size = size.value

        if self.size <= 0:
            error("Array size must be > 0", line=size.position)
        elif not isinstance(size.ret_type, Type_I32.Integer_32):
            error("Array size must be an integer", line=size.position)

        self.ir_type = ir.ArrayType(typ.ir_type, self.size)

    @staticmethod
    def convert_from(func, typ: str, previous):
        error(f"type '{typ}' cannot be converted to type 'Array<{typ}>'",
              line=previous.position)

    def convert_to(self, func, orig, typ):
        if typ != self:
            error(f"Cannot convert {self}' " +
                  f"to type '{typ}'", line=orig.position)
        return orig.eval(func)

    def get_op_return(self, func, op, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        if op == "ind":
            return self.typ

    def get_member_info(self, lhs, rhs):
        match rhs.var_name:
            case "length":
                return MemberInfo(False, False, Type_I32.Integer_32())
            case _:
                error("member not found!", line=rhs.position)

    def get_member(self, func, lhs, rhs):
        match rhs.var_name:
            case "length":
                return ir.Constant(ir.IntType(32), self.size)
            case _:
                error("member not found!", line=rhs.position)

    def __eq__(self, other):
        if (other is None) or other.name != self.name:
            return False

        return other.typ == self.typ and other.size == self.size

    def __neq__(self, other):
        if (other is None) or other.name != self.name:
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

    def get_iter_return(self, loc):
        return ItemIterator(self)

    def create_iterator(self, func, val, loc):
        iter_type = ItemIterator(self)
        ptr = func.create_const_var(iter_type)

        data_ptr_ptr = func.builder.gep(ptr,
                                        [ir.Constant(ir.IntType(32), 0),
                                         ir.Constant(ir.IntType(32), 0)])
        current_ptr = func.builder.gep(ptr,
                                       [ir.Constant(ir.IntType(32), 0),
                                        ir.Constant(ir.IntType(32), 1)])
        size_ptr = func.builder.gep(ptr,
                                    [ir.Constant(ir.IntType(32), 0),
                                     ir.Constant(ir.IntType(32), 2)])

        func.builder.store(val.get_ptr(func), data_ptr_ptr)
        func.builder.store(ir.Constant(ir.IntType(32), 0), current_ptr)
        func.builder.store(ir.Constant(ir.IntType(32), self.size), size_ptr)

        return ptr

    def add_ref_count(self, func, ptr):
        int_type = ir.IntType(64)
        zero_const = ir.Constant(int_type, 0)
        array_ptr = ptr.get_ptr(func)

        if not self.ref_counted:
            pass

        for i in range(self.size):
            index = ir.Constant(int_type, i)
            p = func.builder.gep(array_ptr, [zero_const, index])
            node = PassNode(ptr.position, None, self.typ, ptr=p)
            self.typ.add_ref_count(func, node)

    def dispose(self, func, ptr):
        int_type = ir.IntType(64)
        zero_const = ir.Constant(int_type, 0)
        array_ptr = ptr.get_ptr(func)
        for i in range(self.size):
            index = ir.Constant(int_type, i)
            p = func.builder.gep(array_ptr, [zero_const, index])
            node = PassNode(ptr.position, None, self.typ, ptr=p)
            self.typ.dispose(func, node)


class ItemIterator(Type_Base.Type):
    __slots__ = ("iter_ret", "ir_type")
    is_iterator = True
    returnable = False

    name = "ItemIter"

    def __init__(self, collection_type):
        self.iter_ret = collection_type.typ
        # {data_ptr: *T, current: i32, size: i32}
        self.ir_type = ir.LiteralStructType((collection_type.ir_type.as_pointer(),
                                             ir.IntType(32),
                                             ir.IntType(32)))

    def get_iter_return(self, loc):
        return self.iter_ret

    def iter_condition(self, func, self_ptr, loc):
        end_ptr = func.builder.gep(self_ptr,
                                   [ir.Constant(ir.IntType(32), 0),
                                    ir.Constant(ir.IntType(32), 2)])
        current_ptr = func.builder.gep(self_ptr,
                                       [ir.Constant(ir.IntType(32), 0),
                                        ir.Constant(ir.IntType(32), 1)])
        end_val = func.builder.load(end_ptr)
        current_val = func.builder.load(current_ptr)
        return func.builder.icmp_signed("<", current_val, end_val)

    def iter(self, func, self_ptr, loc):
        current_ptr = func.builder.gep(self_ptr,
                                       [ir.Constant(ir.IntType(32), 0),
                                        ir.Constant(ir.IntType(32), 1)])
        current_val = func.builder.load(current_ptr)
        addition = func.builder.add(current_val, ir.Constant(ir.IntType(32), 1))
        func.builder.store(addition, current_ptr)
        value_ptr_ptr = func.builder.gep(self_ptr,
                                         [ir.Constant(ir.IntType(32), 0),
                                          ir.Constant(ir.IntType(32), 0)])
        val_ptr_val = func.builder.load(value_ptr_ptr)
        value_ptr = func.builder.gep(val_ptr_val,
                                     [ir.Constant(ir.IntType(32), 0),
                                      addition])
        value = func.builder.load(value_ptr)
        return value

    def iter_get_val(self, func, self_ptr, loc):
        current_ptr = func.builder.gep(self_ptr,
                                       [ir.Constant(ir.IntType(32), 0),
                                        ir.Constant(ir.IntType(32), 1)])
        current_val = func.builder.load(current_ptr)
        value_ptr_ptr = func.builder.gep(self_ptr,
                                         [ir.Constant(ir.IntType(32), 0),
                                          ir.Constant(ir.IntType(32), 0)])
        val_ptr_val = func.builder.load(value_ptr_ptr)
        value_ptr = func.builder.gep(val_ptr_val,
                                     [ir.Constant(ir.IntType(32), 0),
                                      current_val])
        value = func.builder.load(value_ptr)
        return value
