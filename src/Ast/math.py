from collections import deque
from typing import Any, Callable, Final, NamedTuple

from llvmlite import ir

import errors
from Ast.Ast_Types.Type_Reference import Reference
# from Ast import exception
# from Ast.literals import Literal
from Ast.nodes import ASTNode, ExpressionNode
from Ast.nodes.commontypes import SrcPosition
from Ast.variables.variablereference import VariableRef

# from Ast.variable import VariableRef

ZERO_CONST: Final = ir.Constant(ir.IntType(64), 0)

ops: dict[str, 'Operation'] = dict()


class Operation(NamedTuple):
    operator_precendence: int
    name: str
    right_asso: bool
    function: Callable[[ASTNode, ASTNode, Any, Any], ir.Instruction|None]
    cls: Callable
    pre_eval_right: bool = True,

    def __call__(self, pos, lhs, rhs, shunted=False):
        return self.cls(pos, self, lhs, rhs, shunted)


class OperationNode(ExpressionNode):
    '''Operation class to define common behavior in Operations'''
    __slots__ = ("op", "shunted", "lhs", "rhs")
    is_operator = True

    def __init__(self, pos: SrcPosition, op, lhs, rhs, shunted = False):
        super().__init__(pos)
        self.lhs     = lhs
        self.rhs     = rhs
        self.shunted = shunted
        self.op      = op

    @property
    def op_type(self):
        return self.op.name

    @property
    def operator_precendence(self):
        return self.op.operator_precendence

    @property
    def right_asso(self) -> bool:
        return self.op.right_asso

    def deref(self, func):
        # TODO: NONE CHECK COULD BE REDUNDENT
        if self.rhs.ret_type is not None and isinstance(self.rhs.ret_type, Reference):
            self.rhs = self.rhs.get_value(func)
        if self.lhs.ret_type is not None and isinstance(self.lhs.ret_type, Reference):
            self.lhs = self.lhs.get_value(func)

    def pre_eval(self, func):
        self.lhs.pre_eval(func)
        if self.op.pre_eval_right:
            self.rhs.pre_eval(func)

        self.deref(func)

        if self.op.name=="as":
            self.rhs.eval(func)
            self.ret_type = self.rhs.ret_type
        else:
            self.ret_type = (self.lhs.ret_type).get_op_return(self.op_type, self.lhs, self.rhs)
        if self.ret_type!=None:
            self.ir_type = self.ret_type.ir_type

    def eval_math(self, func, lhs, rhs):
        return self.op.function(self, func, lhs, rhs)

    def right_handed_position(self):
        '''get the position of the right handed element. This is recursive'''
        return self.rhs.position

    def eval(self, func):
        if not self.shunted:
            return RPN_to_node(shunt(self)).eval(func)
        else:
            self.pre_eval(func)
            return self.eval_math(func, self.lhs, self.rhs)

    def __str__(self) -> str:
        return f"<{str(self.lhs)} |{self.op.name}| {str(self.rhs)}>"

    def as_type_reference(self):
        if not self.shunted:
            print("BAMING")
            return RPN_to_node(shunt(self)).as_type_reference_defer()
        else:
            return self.as_type_reference_defer()

    def as_type_reference_defer(self):
        return super().as_type_reference()

# To any future programmers:
#   I am sorry for this shunt() function.
def shunt(node: OperationNode) -> deque:
    # * create stack and queue
    op_stack: deque[tuple[ExpressionNode|OperationNode, int]] = deque()
    output_queue: deque[ExpressionNode|OperationNode] = deque()

    input_queue = deque([node.rhs, node, node.lhs])
    active_node = [node]

    while input_queue:
        item = input_queue.pop()
        if not item.is_operator:
            output_queue.append(item)
        if item.is_operator:
            if item not in active_node:
                input_queue.append(item.rhs)
                input_queue.append(item)
                input_queue.append(item.lhs)
                active_node.append(item)
                continue
            elif item in active_node:
                while op_stack:
                    op = op_stack.pop()
                    if not item.right_asso and op[1] >= item.operator_precendence:
                        output_queue.append(op[0])
                    elif item.right_asso and op[1] > item.operator_precendence:  # right associativity
                        output_queue.append(op[0])
                    else:
                        op_stack.append(op)
                        break
                op_stack.append((item.op_type, item.operator_precendence))

    # * put remaining operators onto the output queue
    op_stack.reverse()
    for op in op_stack:
        output_queue.append(op[0])

    return output_queue


def RPN_to_node(shunted_data: deque) -> OperationNode:
    '''take RPN from shunt function and convert them into new nodes'''
    op_stack: deque[ExpressionNode|OperationNode] = deque()

    while len(shunted_data) > 1:
        stack: deque[tuple[ExpressionNode | OperationNode, int]] = deque()
        for c,x in enumerate(shunted_data):
            if isinstance(x, str):
                r, l = stack.pop(), stack.pop()

                p = ops[x](l[0].position, l[0],r[0], True)

                del shunted_data[c]
                del shunted_data[r[1]]
                del shunted_data[l[1]]

                shunted_data.insert(c-2, p)
                break
            else:
                stack.append((x,c))
    return shunted_data[0]


def operator(precedence: int, name: str, right = False, pre_eval_right = True, cls = OperationNode):
    def wrapper(func):
        global ops
        op = Operation(precedence, name.lower(), right, func, cls, pre_eval_right)
        ops[name.upper()] = op
        ops[name.lower()] = op

        def new_func(self, pos, lhs, rhs, shunted=False):
            '''changes the original function into a factory/generator for OperationNode(pos, op, ...)'''
            return op(pos, lhs, rhs, shunted)

        return new_func
    return wrapper

# class Ref(OperationNode):
#     '''Variable Reference that acts like other `expr` nodes. It returns a ptr uppon `eval`'''
#     __slots__ = ('var', )
#     name = "ref"

#     def __init__(self, pos: SrcPosition, op, var, rhs, shunted = False):

#         super().__init__(pos, op, var, rhs, shunted)
#         self.var = var

#     def pre_eval(self, func):
#         self.var.pre_eval(func)
#         self.ret_type = Ast_Types.Reference(self.var.ret_type)
#         self.ir_type = self.ret_type.ir_type

#     def eval_math(self, func, lhs, rhs):
#         return self.var.get_ptr(func)

#     def get_var(self, func):
#         return self.var.get_var(func)

#     def get_value(self, func):
#         return self.var

#     def get_ptr(self, func):
#         return self.var.get_ptr(func)

#     def __repr__(self) -> str:
#         return f"<Ref to '{self.var}'>"

#     def __str__(self) -> str:
#         return "&"+str(self.var)

#     def as_type_reference_defer(self):
#         return Ast_Types.Reference(self.var.as_type_reference())

# class VariableIndexRef(OperationNode):
#     '''Variable Reference that acts like other `expr` nodes. It returns a value uppon `eval`''' # TODO: use correct doc
#     __slots__ = ('ind', 'varref', 'var_name', 'size')
#     name = "varIndRef"

#     def __init__(self, pos: SrcPosition, op, varref: "VariableRef", ind: ExpressionNode, shunted = False):
#         parenify = ParenthBlock(ind.position)
#         parenify.append_child(ind)
#         super().__init__(pos, op, varref, parenify, shunted)
#         self._position = pos
#         self.varref = varref
#         self.ind = ind
#         if isinstance(ind, ParenthBlock):
#             self.ind = ind.children[0]
#         self.size = 0

#     def pre_eval(self, func):
#         self.varref.pre_eval(func)
#         if self.varref.ret_type.name == "ref":
#             self.varref = self.varref.get_value(func)
#             self.varref.ir_type = self.varref.ret_type.ir_type

#         self.ind.pre_eval(func)
#         if isinstance(self.ind.ret_type.name, Ref):
#             self.ind = self.ind.get_value(func)
#         if self.varref.ret_type.get_op_return('ind', None, self.ind) is not None:
#             self.ret_type = self.varref.ret_type.get_op_return('ind', None, self.ind)
#         else:
#             self.ret_type = self.varref.ret_type
#         self.ir_type = self.ret_type.ir_type

#     def check_valid_literal(self, lhs, rhs):
#         if rhs.name == "literal" and (lhs.ret_type.size-1 < rhs.value or rhs.value < 0): # check inbounds
#             error(f'Array index out range. Max size \'{lhs.ret_type.size}\'', line = rhs.position)

#         if rhs.ret_type.name not in ("i32", "i64", "i16", "i8"):
#             print(rhs)
#             error(f'Array index operation must use an integer index. type used: \'{rhs.ret_type}\'', line = rhs.position)

#     def _out_of_bounds(self, func):
#         '''creates the code for runtime bounds checking'''
#         size = Literal((-1,-1,-1), self.varref.ir_type.count-1, Ast_Types.Integer_32())
#         zero = Literal((-1,-1,-1), 0, Ast_Types.Integer_32())
#         cond = self.ind.ret_type.le(func, size, self.ind)
#         cond2 = self.ind.ret_type.gr(func, zero, self.ind)
#         condcomb = func.builder.or_(cond, cond2)
#         with func.builder.if_then(condcomb) as if_block:
#             exception.over_index_exception(func, self.varref, self.ind.eval(func), self.position)


#     # TODO: fix this painful code. It is so ugly.
#     def get_ptr(self, func) -> ir.Instruction:
#         self.check_valid_literal(self.varref, self.ind)
#         if self.ind.name != "literal":#* error checking at runtime
#             if isinstance(self.ind, OperationNode) and self.ind.ret_type.rang is not None:
#                 rang = self.ind.ret_type.rang
#                 arrayrang = range(0, self.varref.ir_type.count)
#                 if rang[0] in arrayrang and rang[1] in arrayrang: 
#                     return func.builder.gep(self.varref.get_ptr(func) , [ZERO_CONST, self.ind.eval(func),])

#             elif self.ind.get_var(func).range is not None:
#                 rang = self.ind.get_var(func).range
#                 arrayrang = range(0, self.varref.ir_type.count)
#                 if self.ind.name == "varRef" and rang[0] in arrayrang and rang[1] in arrayrang:
#                     return func.builder.gep(self.varref.get_ptr(func) , [ZERO_CONST, self.ind.eval(func),])

#             self._out_of_bounds(func)
#         return func.builder.gep(self.varref.get_ptr(func) , [ZERO_CONST, self.ind.eval(func),])

#     def get_value(self, func):
#         return self.get_ptr(func)

#     def get_var(self, func):
#         return self.varref.get_var(func)

#     def eval_math(self, func, rhs, lhs):
#         return self.varref.ret_type.index(func, self)

#     def __repr__(self) -> str:
#         return f"<index of `{self.varref}`>"

#     def __str__(self) -> str:
#         return "BUNK"

#     def as_type_reference(self):
#         print(self.shunted, self.varref)
#         return super().as_type_reference()

#     def as_type_reference_defer(self):
#         return Ast_Types.Array(self.ind, self.varref.as_type_reference())


# # TODO: have functions be variables that way function-types and callables can be added.
# @operator(11, "call")
# def call(self, func, lhs: VariableRef, rhs):
#     func.module.functions[lhs.name]
#     return (lhs.ret_type).convert_to(func, lhs, rhs.ret_type)

@operator(13, "access_member", pre_eval_right=False)
def member_access(self, func, lhs, rhs):
    if not lhs.ret_type.has_members:
        errors.error("Has no members", line = lhs.right_handed_position())
    return (lhs.ret_type).get_member(func, lhs, rhs)

# @operator(13, "index", cls = VariableIndexRef)
# def index(self, func, lhs, rhs):
#     pass

# @operator(11, "ref", cls=Ref)
# def ref(self, func, lhs, rhs):
#     pass


@operator(10, "as")
def _as(self, func, lhs, rhs):
    return (lhs.ret_type).convert_to(func, lhs, rhs.as_type_reference())


# TODO: get this working (it seems llvm doesn't have a basic `pow` operation, it is a function)
@operator(9, "Pow")
def pow(self, func, lhs, rhs):
    pass


@operator(1, "Sum")
def sum(self, func, lhs, rhs):
    return (lhs.ret_type).sum(func, lhs, rhs)


@operator(1, "Sub")
def sub(self, func, lhs, rhs):
    return (lhs.ret_type).sub(func, lhs, rhs)


@operator(2, "Mul")
def mul(self, func, lhs, rhs):
    return (lhs.ret_type).mul(func, lhs, rhs)


@operator(2, "Div")
def div(self, func, lhs, rhs):
    return (lhs.ret_type).div(func, lhs, rhs)


@operator(2, "Mod")
def mod(self, func, lhs, rhs):
    return (lhs.ret_type).mod(func, lhs, rhs)

# * comparators


@operator(0, "eq")
def eq(self, func, lhs, rhs):
    return (lhs.ret_type).eq(func, lhs, rhs)


@operator(0, "neq")
def neq(self, func, lhs, rhs):
    return (lhs.ret_type).neq(func, lhs, rhs)


@operator(0, "le")
def le(self, func, lhs, rhs):
    return (lhs.ret_type).le(func, lhs, rhs)


@operator(0, "leq")
def leq(self, func, lhs, rhs):
    return (lhs.ret_type).leq(func, lhs, rhs)


@operator(0, "gr")
def gr(self, func, lhs, rhs):
    return (lhs.ret_type).gr(func, lhs, rhs)


@operator(0, "geq")
def geq(self, func, lhs, rhs):
    return (lhs.ret_type).geq(func, lhs, rhs)

# * boolean ops


@operator(-3, "or")
def _or(self, func, lhs, rhs):
    return (lhs.ret_type)._or(func, lhs, rhs)


@operator(-2, "and")
def _and(self, func, lhs, rhs):
    return (lhs.ret_type)._and(func, lhs, rhs)


@operator(-1, "not")
def _not(self, func, lhs, rhs):
    return (lhs.ret_type)._not(func, lhs)

# * Inplace ops (-100 used as precedence to ensure that it is ALWAYS the last operation)


def check_valid_inplace(lhs) -> bool:
    '''check if lhs is a variable ref'''
    return isinstance(lhs, VariableRef) or \
      errors.error("Left-hand-side of inplace operation must be a variable!",
                   line=lhs.position)  # only runs if false!


@operator(-100, "_isum")
def isum(self, func, lhs, rhs):
    check_valid_inplace(lhs)
    return (lhs.ret_type).isum(func, lhs, rhs)


@operator(-100, "_isub")
def isub(self, func, lhs, rhs):
    check_valid_inplace(lhs)
    return (lhs.ret_type).isub(func, lhs, rhs)


@operator(-100, "_imul")
def imul(self, func, lhs, rhs):
    check_valid_inplace(lhs)
    return (lhs.ret_type).imul(func, lhs, rhs)


@operator(-100, "_idiv")
def idiv(self, func, lhs, rhs):
    check_valid_inplace(lhs)
    return (lhs.ret_type).idiv(func, lhs, rhs)
