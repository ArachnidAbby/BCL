from llvmlite import ir

from Ast.Ast_Types.Type_Base import Type
from Ast.nodes.passthrough import PassNode


ZERO_CONST = ir.Constant(ir.IntType(64), 0)


class TupleType(Type):
    __slots__ = ('ir_type', 'member_types', 'size', 'returnable',
                 'needs_dispose', 'ref_counted')

    literal_index = True
    name = "Tuple"

    def __init__(self, member_types):
        self.member_types = member_types
        self.returnable = True
        self.needs_dispose = False
        self.ref_counted = False
        for typ in member_types:
            self.returnable = self.returnable and typ.returnable
            self.needs_dispose = self.needs_dispose or typ.needs_dispose
            self.ref_counted = self.ref_counted or typ.ref_counted

        self.size = len(member_types)
        self.ir_type = ir.LiteralStructType([member.ir_type for member in member_types])

    def get_op_return(self, func, op, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
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

    def index(self, func, lhs, rhs):
        return func.builder.gep(lhs.get_ptr(func),
                                [ZERO_CONST, rhs.eval(func)])

    def put(self, func, lhs, value):
        return func.builder.store(value.eval(func), lhs.get_ptr(func))

    def add_ref_count(self, func, ptr):
        int_type = ir.IntType(64)
        zero_const = ir.Constant(int_type, 0)
        tuple_ptr = ptr.get_ptr(func)
        for i in range(self.size):
            index = ir.Constant(int_type, i)
            typ = self.member_types[i]
            if not typ.ref_counted:
                continue
            p = func.builder.gep(tuple_ptr, [zero_const, index])
            node = PassNode(ptr.position, None, typ, ptr=p)
            typ.add_ref_count(func, node)

    def pop_ref_count(self, func, ptr):
        int_type = ir.IntType(64)
        zero_const = ir.Constant(int_type, 0)
        tuple_ptr = ptr.get_ptr(func)
        for i in range(self.size):
            index = ir.Constant(int_type, i)
            p = func.builder.gep(tuple_ptr, [zero_const, index])
            typ = self.member_types[i]
            node = PassNode(ptr.position, None, typ, ptr=p)
            typ.pop_ref_count(func, node)

    def dispose(self, func, ptr):
        int_type = ir.IntType(64)
        zero_const = ir.Constant(int_type, 0)
        tuple_ptr = ptr.get_ptr(func)
        for i in range(self.size):
            index = ir.Constant(int_type, i)
            typ = self.member_types[i]
            if not typ.needs_dispose:
                continue
            p = func.builder.gep(tuple_ptr, [zero_const, index])
            node = PassNode(ptr.position, None, typ, ptr=p)
            typ.dispose(func, node)
