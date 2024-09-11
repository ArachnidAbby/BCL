from typing import NoReturn

from llvmlite import ir

import errors
from Ast import exception
from Ast.Ast_Types import Type_I32
from Ast.Ast_Types.Type_Base import Type
from Ast.literals.numberliteral import Literal
from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.passthrough import PassNode

ZERO_CONST = ir.Constant(ir.IntType(64), 0)
ONE_CONST = ir.Constant(ir.IntType(64), 1)


class SliceType(Type):
    __slots__ = ("inner_typ", "ir_type",)

    returnable = False
    index_returns_ptr = True

    def __init__(self, inner_typ: Type):
        self.inner_typ = inner_typ

        # (*i8, i32, i32, i8)

        self.ir_type = ir.LiteralStructType(
            (
                ir.PointerType(inner_typ.ir_type),  # Start Pointer
                ir.IntType(32),  # length
                # ? does 'step' need to be that large?
                ir.IntType(32),  # step
                ir.IntType(8)    # reversed (-1 step) (is 1 or -1)
            )
        )

    def __str__(self) -> str:
        return f"[{str(self.inner_typ)}]"

    # ! this has the posibility to emit a runtime error.
    # ! Maybe this should instead return an Optional::<T>
    def convert_to(self, func, orig, typ) -> ir.Instruction | NoReturn:
        from Ast.Ast_Types.Type_Array import Array
        from Ast.Ast_Types.Type_Union import Union
        if isinstance(typ, Union):
            return typ.convert_from(func, self, orig)

        if typ == self:
            return orig.eval(func)

        if not isinstance(typ, Array):
            errors.error("Cannot convert slice to non-array type",
                         line=orig.position)

        return self._convert_to_array(func, orig, typ)

    def _convert_to_array(self, func, orig, typ):
        slice_size = func.builder.zext(self._get_size(func, orig.get_ptr(func)), ir.IntType(64))
        array_size = ir.Constant(ir.IntType(64), typ.size)
        cmp = func.builder.icmp_signed(">", array_size, slice_size)
        with func.builder.if_then(cmp):
            exception.slice_size_exception(func, orig, slice_size, typ.size,
                                           orig.position)

        # loop setup
        step = func.builder.zext(self._get_step(func, orig.get_ptr(func)), ir.IntType(64))
        block_name = func.builder.block._name
        loop_block = func.builder.append_basic_block(f'{block_name}.for')
        loop_after = func.builder.append_basic_block(f'{block_name}.endfor')

        iter_var = func.create_const_var(Type_I32.Integer_32(64, 'i64', Type_I32.I64_RANGE, True))
        output_ptr = func.create_const_var(typ)
        func.builder.store(ZERO_CONST, iter_var)
        multiplier = func.builder.sext(self._get_reversed(func,
                                                          orig.get_ptr(func)),
                                       ir.IntType(64))

        array_ptr = self._get_array_ptr(func, orig.get_ptr(func))

        # actual looping
        func.builder.branch(loop_block)
        func.builder.position_at_start(loop_block)
        iter_val = func.builder.load(iter_var)
        index = func.builder.mul(iter_val, multiplier)

        value = func.builder.load(func.builder.gep(array_ptr,
                                                   [index]))
        output_value_ptr = func.builder.gep(output_ptr,
                                            [ZERO_CONST, iter_val])

        func.builder.store(value, output_value_ptr)

        new_val = func.builder.add(step, iter_val)
        func.builder.store(new_val, iter_var)
        do_looping = func.builder.icmp_signed("<", new_val, array_size)
        func.builder.cbranch(do_looping, loop_block, loop_after)

        func.builder.position_at_start(loop_after)

        return func.builder.load(output_ptr)

    def get_op_return(self, func, op, lhs, rhs):
        self._simple_call_op_error_check(op, lhs, rhs)
        if op == "ind":  # TODO: make this account for slicing
            return self.inner_typ

        # if op == 'eq' or op == 'neq':
        #     if lhs.ret_type != rhs.ret_type:
        #         error(f"{self} can only be compared to {self}",
        #               line=rhs.position)
        #     return Type_Bool.Integer_1()

    def _get_size_ptr(self, func, objptr) -> ir.Instruction:
        '''Gets the size ptr at runtime, this is NOT known at compile-time'''
        return func.builder.gep(objptr, [
            ir.Constant(ir.IntType(32), 0),
            ir.Constant(ir.IntType(32), 1)
        ])

    def _get_size(self, func, objptr) -> ir.Instruction:
        '''Gets the size at runtime, this is NOT known at compile-time'''
        return func.builder.load(self._get_size_ptr(func, objptr))

    def _get_step_ptr(self, func, objptr) -> ir.Instruction:
        '''Gets the step at runtime, this is NOT known at compile-time'''
        return func.builder.gep(objptr, [
            ir.Constant(ir.IntType(32), 0),
            ir.Constant(ir.IntType(32), 2)
        ])

    def _get_array_ptr_ptr(self, func, objptr) -> ir.Instruction:
        '''Gets the array_ptr at runtime, this is NOT known at compile-time'''
        return func.builder.gep(objptr, [
            ir.Constant(ir.IntType(32), 0),
            ir.Constant(ir.IntType(32), 0)
        ])

    def _get_array_ptr(self, func, objptr) -> ir.Instruction:
        '''Gets the array_ptr at runtime, this is NOT known at compile-time'''
        return func.builder.load(self._get_array_ptr_ptr(func, objptr))

    def _get_step(self, func, objptr) -> ir.Instruction:
        '''Gets the step at runtime, this is NOT known at compile-time'''
        return func.builder.load(self._get_step_ptr(func, objptr))

    def _get_reversed_ptr(self, func, objptr) -> ir.Instruction:
        '''Gets the reversed-flag at runtime, this is NOT known at compile-time'''
        return func.builder.gep(objptr, [
            ir.Constant(ir.IntType(32), 0),
            ir.Constant(ir.IntType(32), 3)
        ])

    def _get_reversed(self, func, objptr) -> ir.Instruction:
        '''Gets the reversed-flag at runtime, this is NOT known at compile-time'''
        return func.builder.load(self._get_reversed_ptr(func, objptr))

    def set_length(self, func, objptr, new_length: ir.Constant | ir.Instruction):
        length_ptr = self._get_size_ptr(func, objptr)
        func.builder.store(new_length, length_ptr)

    def _out_of_bounds(self, func, lhs, rhs, val):
        '''creates the code for runtime bounds checking'''
        size = PassNode(SrcPosition.invalid(),
                        self._get_size(func, lhs.get_ptr(func)),
                        Type_I32.Integer_32())
        zero = Literal(SrcPosition.invalid(), 0, Type_I32.Integer_32())
        cond = rhs.ret_type.le(func, rhs, zero)
        cond2 = rhs.ret_type.geq(func, rhs, size)
        condcomb = func.builder.or_(cond, cond2)
        with func.builder.if_then(condcomb) as _:
            exception.over_index_exception(func, lhs,
                                           val, lhs.position)

    def generate_runtime_check(self, func, lhs, rhs):
        '''generates the runtime bounds checking
        depending on the node type of the index operand'''
        if rhs.isconstant and rhs.value < 0:  # check underflow for constants
            errors.error("Literal index out of range.\n" +
                         "Index must be greater than 0",
                         line=rhs.position)

        objptr = lhs.get_ptr(func)
        inner_ptr = self._get_array_ptr(func, objptr)
        step = self._get_step(func, objptr)
        multiplier = func.builder.sext(self._get_reversed(func, objptr),
                                       ir.IntType(32))

        val = rhs.eval(func)
        index = func.builder.mul(val, step)

        ptr = func.builder.gep(inner_ptr,
                               [func.builder.mul(index, multiplier)])
        self._out_of_bounds(func, lhs, rhs, val)
        return ptr

    def index(self, func, lhs, rhs) -> ir.Instruction:
        return self.generate_runtime_check(func, lhs, rhs)
