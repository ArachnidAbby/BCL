from Ast.Ast_Types.Type_Base import Type
from llvmlite import ir
import errors
from Ast.literals.numberliteral import Literal

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

int_types = {
    U8SIZE: ir.IntType(U8SIZE),
    U16SIZE: ir.IntType(U16SIZE),
    U32SIZE: ir.IntType(U32SIZE),
    U64SIZE: ir.IntType(U64SIZE)
}


class EnumType(Type):
    __slots__ = ("ir_type", "enum_name", "members", "namespace")

    name = "Enum"

    def __init__(self, name, namespace, pos, members: list[tuple[str, None | int]]):
        self.enum_name = name
        self.namespace = namespace
        self.members: dict[str, int] = {}

        # Get size and create members. Same way as C enums
        max_size = 0
        last_num = 0
        for mem_name, val in members:
            if val is None:
                val = last_num
            self.members[mem_name] = val
            if val > int_sequence[max_size]:
                max_size += 1

            last_num += 1

        if max_size >= len(int_sequence):
            errors.error("Max bitsize of an enum is 64 bits.\n" +
                         "Please keep values within the u64 range.",
                         line=pos)

        self.ir_type = int_types[int_sequence[max_size]]

    def __eq__(self, other):
        return super().__eq__(other) and self.enum_name == other.enum_name \
               and self.namespace == other.namespace

    def get_namespace_name(self, func, name, pos):
        if name in self.members.keys():
            return Literal(pos, self.members[name], self)

        errors.error(f"Name \"{name}\" cannot be " +
                     f"found in Type \"{self.enum_name}\"",
                     line=pos)
