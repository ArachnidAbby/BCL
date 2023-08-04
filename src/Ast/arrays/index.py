from typing import Final

from llvmlite import ir  # type: ignore

from Ast import Ast_Types, exception
from Ast.literals.numberliteral import Literal
from Ast.math import OperationNode
from Ast.nodes import ExpressionNode
from Ast.nodes.commontypes import Lifetimes, SrcPosition
from Ast.reference import Ref
from Ast.variables.reference import VariableRef
from errors import error

ZERO_CONST: Final = ir.Constant(ir.IntType(64), 0)


def check_in_range(rang, arrayrang):
    return rang[0] in arrayrang and rang[1] in arrayrang


def check_valid_literal_range(lhs, rhs):
    if not lhs.ret_type.generate_bounds_check:
        return

    return rhs.isconstant and \
        (lhs.ret_type.size-1 < rhs.value or rhs.value < 0)


# TODO: RENAME & MAKE INTO MATH EXPRESSION
class VariableIndexRef(ExpressionNode):
    '''The index to an array'''
    __slots__ = ('ind', 'varref', 'var_name', 'size')
    assignable = True

    def __init__(self, pos: SrcPosition, varref: VariableRef,
                 ind: ExpressionNode):
        super().__init__(pos)
        self.varref = varref
        self.ind = ind
        self.size = 0

    def copy(self):
        return VariableIndexRef(self._position, self.varref.copy(), self.ind.copy())

    def fullfill_templates(self, func):
        self.varref.fullfill_templates(func)
        self.ind.fullfill_templates(func)

    def pre_eval(self, func):
        self.varref.pre_eval(func)

        self.ind.pre_eval(func)
        if not self.ind.isconstant and self.varref.ret_type.literal_index:
            error(f"Type \"{str(self.varref.ret_type)}\" can only have " +
                  "literal indexes", line=self.ind.position)

        op_return = self.varref.ret_type.get_op_return(func, 'ind', None, self.ind)
        if op_return is not None:
            self.ret_type = op_return
        else:
            error("Type is not indexable")
            self.ret_type = self.varref.ret_type

    def check_valid_literal(self, lhs, rhs):
        if rhs.isconstant and check_valid_literal_range(lhs, rhs):
            error(f'Array index out range. Max size \'{lhs.ret_type.size}\'',
                  line=rhs.position)

        if rhs.ret_type.name not in ("i32", "i64", "i16", "i8", "u8",
                                     "u16", "u32", "u64"):
            error("Array index operation must use an integer index." +
                  f"type used: '{rhs.ret_type}'", line=rhs.position)

    def get_ptr(self, func) -> ir.Instruction:
        if self.ptr is None:
            if isinstance(self.ind.ret_type, Ref):
                self.ind = self.ind.get_value(func)
            self.ptr = self.varref.ret_type.index(func, self.varref, self.ind)
        return self.ptr

    def get_value(self, func):
        return self.get_ptr(func)

    def get_var(self, func):
        return self.varref.get_var(func)

    def eval_impl(self, func):
        if isinstance(self.ind.ret_type, Ref):
            self.ind = self.ind.get_value(func)
        self.ptr = self.varref.ret_type.index(func, self.varref, self.ind)
        if self.ret_type.name == "UntypedPointer":
            return self.ptr

        return func.builder.load(self.ptr)

    def get_lifetime(self, func):
        return self.varref.get_lifetime(func)

    def __repr__(self) -> str:
        return f"<index of `{self.varref}`>"

    def as_type_reference(self, func, allow_generics=False):
        return Ast_Types.Array(self.ind, self.varref.as_type_reference(func, allow_generics=allow_generics))

    def repr_as_tree(self) -> str:
        return self.create_tree("Array Index",
                                item=self.varref,
                                index=self.ind,
                                return_type=self.ret_type)
