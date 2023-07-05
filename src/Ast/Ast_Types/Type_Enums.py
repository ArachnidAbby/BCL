from Ast.Ast_Types.Type_Base import Type
from llvmlite import ir
from Ast.Ast_Types.Type_I32 import Integer_32
import errors
from Ast.literals.numberliteral import Literal
from Ast import Ast_Types

# Found using https://mathiasbynens.be/demo/integer-range
# because I'm lazy
U8SIZE = 255
U16SIZE = 65535
U32SIZE = 4294967295
U64SIZE = 18446744073709551615

int_sequence = [
    U8SIZE,
    U16SIZE,
    U32SIZE,
    U64SIZE
]

int_sequence_sizes = [
    8,
    16,
    32,
    64
]

int_types = {
    U8SIZE: ir.IntType(8),
    U16SIZE: ir.IntType(16),
    U32SIZE: ir.IntType(32),
    U64SIZE: ir.IntType(64)
}


class EnumType(Type):
    __slots__ = ("ir_type", "enum_name", "members", "namespace", "bitsize")

    name = "Enum"

    def __init__(self, name, namespace, pos, members: list[tuple[str, "SrcPosition"]]):
        self.enum_name = name
        self.namespace = namespace
        self.members: dict[str, int | None] = {}

        for mem_name, val_pos in members:
            if mem_name in self.members.keys():
                errors.error("Variant already defined",
                             line=val_pos)
            self.members[mem_name] = None

    def create_values(self, func, members: list[tuple[str, None | int, "SrcPosition"]], pos):
        max_size = 0
        last_num = 0
        # Get size and create members. Same way as C enums
        for mem_name, val, val_pos in members:

            if val is None:
                val = last_num
            else:
                val.pre_eval(func)
                val = val.get_var(func).value

            self.members[mem_name] = val
            if val > int_sequence[max_size]:
                max_size += 1
                if max_size >= len(int_sequence):
                    errors.error("Max bitsize of an enum is 64 bits.\n" +
                                 "Please keep values within the u64 range.",
                                 line=pos)
                self.bitsize = int_sequence_sizes[max_size]
                self.ir_type = int_types[int_sequence[max_size]]

            last_num = val + 1

        self.bitsize = int_sequence_sizes[max_size]
        self.ir_type = int_types[int_sequence[max_size]]


    def convert_to(self, func, orig, typ):
        if typ == self:
            return orig.eval(func)

        if isinstance(typ, Integer_32):
            if typ.size == self.bitsize:
                return orig.eval(func)
            elif typ.size > self.bitsize:
                if typ.signed:
                    return func.builder.sext(orig.eval(func), typ.ir_type)
                return func.builder.zext(orig.eval(func), typ.ir_type)
            if typ.size < self.bitsize:
                return func.builder.trunc(orig.eval(func), typ.ir_type)

        errors.error(f"Cannot convert {str(self)} to {str(typ)}",
                     line=orig.position)

    def get_op_return(self, op: str, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        match op.lower():
            case 'eq' | 'neq':
                return Ast_Types.Type_Bool.Integer_1()

    def eq(self, func, lhs, rhs):
        if rhs.ret_type != self:
            errors.error(f"Can only compare \"{self}\" " +
                         f"to \"{self}\" not \"{rhs.ret_type}\"",
                         line=rhs.position)
        return func.builder.icmp_signed('==', lhs.eval(func), rhs.eval(func))

    def neq(self, func, lhs, rhs):
        if rhs.ret_type != self:
            errors.error(f"Can only compare \"{self}\" " +
                         f"to \"{self}\" not \"{rhs.ret_type}\"",
                         line=rhs.position)
        return func.builder.icmp_signed('!=', lhs.eval(func), rhs.eval(func))

    def __eq__(self, other):
        return super().__eq__(other) and self.enum_name == other.enum_name \
               and self.namespace == other.namespace

    def __neq__(self, other):
        return super().__eq__(other) or self.enum_name != other.enum_name \
               or self.namespace != other.namespace

    def __hash__(self):
        return hash(f"Enum.{self.enum_name}.{self.namespace}")

    def __str__(self):
        return f"{self.enum_name}(u{self.bitsize})"

    def get_namespace_name(self, func, name, pos):
        if name in self.members.keys():
            if self.members[name] is None:
                errors.error("Variant has yet to be initialized",
                             line=pos)
            return Literal(pos, self.members[name], self)

        errors.error(f"Name \"{name}\" cannot be " +
                     f"found in Type \"{str(self)}\"",
                     line=pos)
