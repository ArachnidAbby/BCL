from typing import Final

from llvmlite import ir

from Ast import Ast_Types, exception
from Ast.literals.numberliteral import Literal
from Ast.math import OperationNode
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import SrcPosition
from Ast.reference import Ref
from Ast.variables.variablereference import VariableRef
from errors import error

ZERO_CONST: Final = ir.Constant(ir.IntType(64), 0)


class VariableIndexRef(ExpressionNode):  # TODO: RENAME & MAKE INTO MATH EXPRESSION
    '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`''' # TODO: add correct doc
    __slots__ = ('ind', 'varref', 'var_name', 'size')
    name = "varIndRef"

    def __init__(self, pos: SrcPosition, varref: VariableRef, ind: ExpressionNode):
        self._position = pos
        self.varref = varref
        self.ind = ind
        self.size = 0

    def pre_eval(self, func):
        self.varref.pre_eval(func)
        if self.varref.ret_type.name == "ref":
            self.varref = self.varref.get_value(func)
            self.varref.ir_type = self.varref.ret_type.ir_type

        self.ind.pre_eval(func)
        if isinstance(self.ind.ret_type.name, Ref):
            self.ind = self.ind.get_value(func)
        if self.varref.ret_type.get_op_return('ind', None, self.ind) is not None:
            self.ret_type = self.varref.ret_type.get_op_return('ind', None, self.ind)
        else:
            self.ret_type = self.varref.ret_type
        self.ir_type = self.ret_type.ir_type

    def check_valid_literal(self, lhs, rhs):
        if rhs.constant and (lhs.ret_type.size-1 < rhs.value or rhs.value < 0):  # check inbounds
            error(f'Array index out range. Max size \'{lhs.ret_type.size}\'',
                  line=rhs.position)

        if rhs.ret_type.name not in ("i32", "i64", "i16", "i8"):
            error(f'Array index operation must use an integer index. \
                  type used: \'{rhs.ret_type}\'', line=rhs.position)

    def _out_of_bounds(self, func):
        '''creates the code for runtime bounds checking'''
        size = Literal((-1,-1,-1), self.varref.ir_type.count-1, Ast_Types.Integer_32())
        zero = Literal((-1,-1,-1), 0, Ast_Types.Integer_32())
        cond = self.ind.ret_type.le(func, size, self.ind)
        cond2 = self.ind.ret_type.gr(func, zero, self.ind)
        condcomb = func.builder.or_(cond, cond2)
        with func.builder.if_then(condcomb) as if_block:
            exception.over_index_exception(func, self.varref, self.ind.eval(func), self.position)

    # TODO: fix this painful code. It is so ugly.
    def get_ptr(self, func) -> ir.Instruction:
        self.check_valid_literal(self.varref, self.ind)
        if not self.ind.constant:  #* error checking at runtime
            if isinstance(self.ind, OperationNode) and self.ind.ret_type.rang is not None:
                rang = self.ind.ret_type.rang
                arrayrang = range(0, self.varref.ir_type.count)
                if rang[0] in arrayrang and rang[1] in arrayrang:
                    return func.builder.gep(self.varref.get_ptr(func), [ZERO_CONST, self.ind.eval(func),])

            elif self.ind.get_var(func).range is not None:
                rang = self.ind.get_var(func).range
                arrayrang = range(0, self.varref.ir_type.count)
                if isinstance(self.ind, VariableRef) and rang[0] in arrayrang and rang[1] in arrayrang:
                    return func.builder.gep(self.varref.get_ptr(func), [ZERO_CONST, self.ind.eval(func)])

            self._out_of_bounds(func)
        return func.builder.gep(self.varref.get_ptr(func), [ZERO_CONST, self.ind.eval(func)])

    def get_value(self, func):
        return self.get_ptr(func)

    def get_var(self, func):
        return self.varref.get_var(func)

    def eval(self, func):
        return self.varref.ret_type.index(func, self)

    def __repr__(self) -> str:
        return f"<index of `{self.varref}`>"

    def as_type_reference(self):
        return Ast_Types.Array(self.ind, self.varref.as_type_reference())
