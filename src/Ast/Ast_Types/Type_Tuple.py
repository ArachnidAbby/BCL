from llvmlite import ir

from Ast.Ast_Types.Type_Base import Type


class TupleType(Type):
    __slots__ = ('ir_type', 'member_types', 'size')

    literal_index = True
    name = "Tuple"

    def __init__(self, member_types):
        self.member_types = member_types
        self.size = len(member_types)
        self.ir_type = ir.LiteralStructType([member.ir_type for member in member_types])

    def get_op_return(self, op, lhs, rhs):
        if op == "ind":
            # assumes rhs is a Literal
            return self.member_types[rhs.value]

    def __eq__(self, other):
        return (other is not None) and self.name == other.name and \
            self.member_types == other.member_types

    def __neq__(self, other):
        return other is None or self.name != other.name or \
            self.member_types != other.member_types

    def __str__(self) -> str:
        return f"({','.join((str(mem) for mem in self.member_types))})"

    def index(self, func, lhs):
        return func.builder.load(lhs.get_ptr(func))

    def put(self, func, lhs, value):
        return func.builder.store(value.eval(func), lhs.get_ptr(func))
