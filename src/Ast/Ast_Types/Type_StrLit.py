from typing import Self

from llvmlite import ir

from Ast.Ast_Types import Type_Bool, Type_Char, Type_I32
from Ast.Ast_Types.Type_Function import MockFunction
from Ast.nodes.commontypes import MemberInfo, SrcPosition
from Ast.nodes.passthrough import PassNode
from errors import error

from . import Type_Base


ZERO_CONST = ir.Constant(ir.IntType(32), 0)
u64_ty = Type_I32.Integer_32(size=64, signed=False, rang=Type_I32.I64_RANGE)


def create_compare_method(typ, module, name, res, res_end):
    bool_ty = ir.IntType(1)
    function_ty = ir.FunctionType(bool_ty,
                                  (typ.ir_type, typ.ir_type))
    func = ir.Function(module.module, function_ty, f"strlit.__meth.__{name}__")
    block = func.append_basic_block(name="entry")
    builder = ir.IRBuilder(block)
    lhs, rhs = func.args[0], func.args[1]
    mock_func = MockFunction(builder, module)
    lhs_ptr = builder.alloca(typ.ir_type)
    rhs_ptr = builder.alloca(typ.ir_type)
    builder.store(lhs, lhs_ptr)
    builder.store(rhs, rhs_ptr)

    lhs_ptr_char = builder.load(builder.gep(lhs_ptr, (ZERO_CONST, ZERO_CONST)))
    rhs_ptr_char = builder.load(builder.gep(rhs_ptr, (ZERO_CONST, ZERO_CONST)))

    size_neq_block = builder.append_basic_block(name="size_neq")
    size_eq_block = builder.append_basic_block(name="size_eq")

    lhs_size = typ.get_size(mock_func, lhs_ptr)
    rhs_size = typ.get_size(mock_func, rhs_ptr)
    cond = builder.icmp_unsigned('!=', lhs_size, rhs_size)

    builder.cbranch(cond, size_neq_block, size_eq_block)
    builder.position_at_end(size_neq_block)
    builder.ret(ir.Constant(bool_ty, res))

    builder.position_at_end(size_eq_block)
    ind_ptr = builder.alloca(u64_ty.ir_type)
    builder.store(ir.Constant(u64_ty.ir_type, 0), ind_ptr)

    loop_block = builder.append_basic_block(name="item_loop")
    neq_block = builder.append_basic_block(name="item_neq")
    eq_block = builder.append_basic_block(name="item_eq")
    after_block = builder.append_basic_block(name="success")

    cond = builder.icmp_unsigned('<', ir.Constant(u64_ty.ir_type, 0), lhs_size)
    builder.cbranch(cond, loop_block, after_block)

    builder.position_at_end(loop_block)
    index = builder.load(ind_ptr)
    ileft_ptr = builder.gep(lhs_ptr_char, [index])
    iright_ptr = builder.gep(rhs_ptr_char, [index])
    ileft_val = builder.load(ileft_ptr)
    iright_val = builder.load(iright_ptr)

    cond = builder.icmp_unsigned('!=', ileft_val, iright_val)
    builder.cbranch(cond, neq_block, eq_block)

    builder.position_at_end(neq_block)
    builder.ret(ir.Constant(bool_ty, res))

    builder.position_at_end(eq_block)

    new_index = builder.add(ir.Constant(u64_ty.ir_type, 1), index)
    builder.store(new_index, ind_ptr)

    cond = builder.icmp_unsigned('<', new_index, lhs_size)
    builder.cbranch(cond, loop_block, after_block)

    builder.position_at_end(after_block)
    builder.ret(ir.Constant(bool_ty, res_end))

    return func


class StringLiteral(Type_Base.Type):
    __slots__ = ('size', 'typ', 'ir_type', 'equal_func', 'nequal_func')
    name = "strlit"
    pass_as_ptr = False
    no_load = False
    returnable = False
    has_members = True

    def __init__(self, module, size=None):
        self.typ = Type_Char.Char()

        if size is not None and not size.isconstant:
            error("size of strlit type must be a int-literal",
                  line=size.position)

        if size is not None:
            self.size = size.value
            if self.size <= 0:
                error("Strlit size must be > 0",
                      line=size.position)
            elif not isinstance(size.ret_type, Type_I32.Integer_32):
                error("Strlit size must be an integer",
                      line=size.position)

        else:
            self.size = size

        self.ir_type = ir.LiteralStructType((ir.IntType(8).as_pointer(),))
        self.equal_func = create_compare_method(self, module, 'eq', 0, 1)
        self.nequal_func = create_compare_method(self, module, 'neq', 1, 0)

    def declare(self, module):
        eq_typ = self.equal_func.ftype
        neq_typ = self.nequal_func.ftype

        ir.Function(module.module, eq_typ, "strlit.__meth.__eq__")
        ir.Function(module.module, neq_typ, "strlit.__meth.__neq__")

    @staticmethod
    def convert_from(func, typ: str, previous):
        error(f"type '{typ}' cannot be converted to type 'Array<{typ}>'",
              line=previous.position)

    def convert_to(self, func, orig, typ):
        if typ != self:
            error(f"Cannot convert 'Array<{orig.ir_type.element}>'" +
                  f"to type '{typ}'", line=orig.position)
        return orig.eval(func)

    def get_op_return(self, func, op, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        if op == "ind":
            return self.typ
        if op == 'eq' or op == 'neq':
            if lhs.ret_type != rhs.ret_type:
                error("strlit can only be compared to another strlit type",
                      line=rhs.position)
            return Type_Bool.Integer_1()

    def get_member_info(self, lhs, rhs):
        match rhs.var_name:
            case "length":
                return MemberInfo(False, False, u64_ty)
            case _:
                error("member not found!", line=rhs.position)

    def get_size(self, func, ptr):
        char_ptr = func.builder.load(func.builder.gep(ptr, (ZERO_CONST, ZERO_CONST)))
        # * This manual placement of the size (8) could be problematic
        # * for future targets
        size_start_ptr = func.builder.gep(char_ptr, (ir.Constant(ir.IntType(32), -8), ))
        size_ptr = func.builder.bitcast(size_start_ptr, ir.IntType(64).as_pointer())
        return func.builder.load(size_ptr)

    def get_member(self, func, lhs, rhs):
        match rhs.var_name:
            case "length":
                ptr = lhs.get_ptr(func)
                return self.get_size(func, ptr)
            case _:
                error("member not found!", line=rhs.position)

    def index(self, func, lhs, rhs):
        lhs_ptr = lhs.get_ptr(func)
        lhs_ptr_char = func.builder.load(func.builder.gep(lhs_ptr, (ZERO_CONST, ZERO_CONST)))
        self.generate_runtime_check(func, lhs, rhs, lhs_ptr)
        return func.builder.gep(lhs_ptr_char,
                                [rhs.eval(func)])

    def _out_of_bounds(self, func, lhs, rhs, val, lhs_ptr):
        '''creates the code for runtime bounds checking'''
        from Ast.literals.numberliteral import Literal
        from Ast import exception  # type: ignore
        size = PassNode(SrcPosition.invalid(),
                        self.get_size(func, lhs_ptr),
                        u64_ty)
        zero = Literal(SrcPosition.invalid(), 0, Type_I32.Integer_32())
        cond = rhs.ret_type.leq(func, size, rhs)
        cond2 = rhs.ret_type.gr(func, zero, rhs)
        condcomb = func.builder.or_(cond, cond2)
        with func.builder.if_then(condcomb) as _:
            exception.over_index_exception(func, lhs,
                                           rhs.eval(func), lhs.position)
        return

    def generate_runtime_check(self, func, lhs, rhs, lhs_ptr):
        '''generates the runtime bounds checking
        depending on the node type of the index operand'''
        lhs_ptr_char = func.builder.load(func.builder.gep(lhs_ptr, (ZERO_CONST, ZERO_CONST)))
        ptr = func.builder.gep(lhs_ptr_char,
                               [rhs.eval(func)])
        val = func.builder.load(ptr)
        self._out_of_bounds(func, lhs, rhs, val, lhs_ptr)
        return ptr

    def eq(self, func, lhs, rhs):
        out = func.builder.call(self.equal_func, (lhs.eval(func), rhs.eval(func)))
        return out

    def neq(self, func, lhs, rhs):
        out = func.builder.call(self.nequal_func, (lhs.eval(func), rhs.eval(func)))
        return out

    def assign(self, func, ptr, value, typ: Self):
        val = value.ret_type.convert_to(func, value, typ)  # type: ignore
        val = func.builder.bitcast(val, self.ir_type)
        func.builder.store(val, ptr.ptr)
