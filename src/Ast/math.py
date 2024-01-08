from collections import deque
from typing import Any, Callable, Final, NamedTuple

from llvmlite import ir

import errors
from Ast import Ast_Types  # type: ignore
from Ast.Ast_Types.Type_Reference import Reference
from Ast.Ast_Types.Type_Void import Void
# from Ast import exception
# from Ast.literals import Literal
from Ast.nodes import ASTNode, ExpressionNode
from Ast.nodes.commontypes import Lifetimes, SrcPosition
from Ast.nodes.passthrough import PassNode

# from Ast.variable import VariableRef

ZERO_CONST: Final = ir.Constant(ir.IntType(64), 0)

ops: dict[str, 'Operation'] = dict()


class Operation(NamedTuple):
    operator_precendence: int
    name: str
    right_asso: bool
    function: Callable[[ASTNode, ASTNode, Any, Any], ir.Instruction | None]
    cls: Callable
    pre_eval_right: bool = True

    def __call__(self, pos, lhs, rhs, shunted=False):
        return self.cls(pos, self, lhs, rhs, shunted)


class OperationNode(ExpressionNode):
    '''Operation class to define common behavior in Operations'''
    __slots__ = ("op", "shunted", "lhs", "rhs")
    is_operator = True

    def __init__(self, pos: SrcPosition, op, lhs, rhs, shunted=False):
        super().__init__(pos)
        self.lhs = lhs
        self.rhs = rhs
        self.shunted = shunted
        self.op = op

    def copy(self):
        return OperationNode(self._position, self.op, self.lhs.copy(), self.rhs.copy(), self.shunted)

    def reset(self):
        super().reset()
        self.lhs.reset()
        self.rhs.reset()
        self.ret_type = Void()

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
        if isinstance(self.lhs.ret_type, Reference):
            if self.lhs.ret_type.typ.name == "STRUCT":
                return

        if isinstance(self.rhs.ret_type, Reference):

            ptr = self.rhs.eval(func)

            self.rhs = PassNode(self.rhs.position,
                                func.builder.load(ptr),
                                self.rhs.ret_type.typ,
                                ptr)

    def pre_eval_math(self, func):
        self.lhs.pre_eval(func)
        if self.op.pre_eval_right:
            self.rhs.pre_eval(func)

        if self.op.name != "as":
            self.deref(func)

        # TODO: Allow an override_get_return Callable
        if self.op.name == "as":
            self.ret_type = self.rhs.as_type_reference(func)
        elif self.op.name in ('not', 'and', 'or'):
            self.ret_type = Ast_Types.Integer_1()
        else:
            self.ret_type = (self.lhs.ret_type).get_op_return(func,
                                                              self.op_type,
                                                              self.lhs,
                                                              self.rhs)

    def eval_math(self, func, lhs, rhs):
        return self.op.function(self, func, lhs, rhs)

    def right_handed_position(self):
        '''get the position of the right handed element. This is recursive'''
        return self.rhs.position

    def fullfill_templates(self, func):
        self.lhs.fullfill_templates(func)
        self.rhs.fullfill_templates(func)

    def post_parse_math(self, func):
        self.lhs.post_parse(func)
        self.rhs.post_parse(func)

    def post_parse(self, func):
        if not self.shunted:
            new = RPN_to_node(shunt(self))
            self.shunted = True
            self.lhs = new.lhs
            self.rhs = new.rhs
            self.op = new.op
            self.post_parse(func)
        else:
            self.post_parse_math(func)

    def pre_eval(self, func):
        if not self.shunted:
            new = RPN_to_node(shunt(self))
            self.shunted = True
            self.lhs = new.lhs
            self.rhs = new.rhs
            self.op = new.op
            self.pre_eval(func)
        else:
            self.pre_eval_math(func)

    def get_ptr(self, func):
        if self.op.name == 'as' and isinstance(self.ret_type, Ast_Types.Reference):
            return self.eval(func)
        else:
            return super().get_ptr(func)

    def eval_impl(self, func):
        if not self.shunted:
            return RPN_to_node(shunt(self)).eval(func)
        else:
            self.pre_eval(func)
            return self.eval_math(func, self.lhs, self.rhs)

    def __str__(self) -> str:
        return f"<{str(self.lhs)} |{self.op.name}| {str(self.rhs)}>"

    def as_type_reference(self, func, allow_generics=False):
        if not self.shunted:
            return RPN_to_node(shunt(self)).as_type_reference_defer(func, allow_generics)
        else:
            return self.as_type_reference_defer(func, allow_generics)

    def as_type_reference_defer(self, func, allow_generics):
        return super().as_type_reference(func, allow_generics)

    def get_lifetime(self, func):
        if self.op.name == "as":
            return self.lhs.get_lifetime(func)

        return Lifetimes.FUNCTION

    def get_coupled_lifetimes(self, func) -> list:
        if self.op.name == "as":
            return self.lhs.get_coupled_lifetimes(func)

        return []

    def repr_as_tree(self) -> str:
        return self.create_tree("Math Expression",
                                lhs=self.lhs,
                                rhs=self.rhs,
                                operation=self.op.name,
                                return_type=self.ret_type)


# To any future programmers:
#   I am sorry for this shunt() function.
def shunt(node: OperationNode) -> deque:
    # * create stack and queue
    op_stack: deque[tuple[ExpressionNode | OperationNode, int]] = deque()
    output_queue: deque[ExpressionNode | OperationNode] = deque()

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
                    if not item.right_asso and \
                            op[1] >= item.operator_precendence:
                        output_queue.append(op[0])
                    # right associativity
                    elif item.right_asso and \
                            op[1] > item.operator_precendence:
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
    # op_stack: deque[ExpressionNode|OperationNode] = deque()

    while len(shunted_data) > 1:
        stack: deque[tuple[ExpressionNode | OperationNode, int]] = deque()
        for c, selected in enumerate(shunted_data):
            if isinstance(selected, str):
                rhs, lhs = stack.pop(), stack.pop()

                p = ops[selected](lhs[0].position, lhs[0], rhs[0], True)

                del shunted_data[c]
                del shunted_data[rhs[1]]
                del shunted_data[lhs[1]]

                shunted_data.insert(c-2, p)
                break
            else:
                stack.append((selected, c))
    return shunted_data[0]


def operator(precedence: int, name: str, right=False,
             pre_eval_right=True, cls=OperationNode):
    def wrapper(func):
        global ops
        op = Operation(precedence, name.lower(), right, func, cls,
                       pre_eval_right)
        ops[name.upper()] = op
        ops[name.lower()] = op

        def new_func(self, pos, lhs, rhs, shunted=False):
            '''changes the original function into a factory/generator
            for OperationNode(pos, op, ...)'''
            return op(pos, lhs, rhs, shunted)

        return new_func
    return wrapper


class MemberAccess(OperationNode):
    __slots__ = ("assignable", "is_pointer")
    # do_register_dispose = False

    def __init__(self, pos: SrcPosition, op, lhs, rhs, shunted=False):
        from Ast.namespace import NamespaceIndex
        from Ast.nodes.container import ContainerNode
        from Ast.variables.reference import VariableRef
        super().__init__(pos, op, lhs, rhs, shunted)
        self.assignable = True
        self.is_pointer = False
        if not isinstance(rhs, ContainerNode) and not isinstance(rhs, VariableRef) and not isinstance(rhs, NamespaceIndex):
            errors.error("Member access operator can only get members that " +
                         "are in parenthesis or are valid keywords",
                         line=rhs.position)
        if isinstance(rhs, ContainerNode) and len(rhs.children) > 1:
            errors.error("Member Access operator using parenthesis must " +
                         "only contain a singlular item.",
                         line=rhs.position)

    def copy(self):
        out = MemberAccess(self._position, self.op, self.lhs.copy(), self.rhs.copy(), self.shunted)
        out.assignable = self.assignable
        out.is_pointer = self.is_pointer
        return out

    def reset(self):
        super().reset()
        self.lhs.reset()
        self.rhs.reset()

    def pre_eval_math(self, func):
        from Ast.nodes.container import ContainerNode

        self.lhs.pre_eval(func)
        lhs = self.lhs
        rhs = self.rhs

        if isinstance(rhs, ContainerNode):
            possible_func = rhs.children[0].get_var(func)
            if possible_func is not None:
                self.ret_type = possible_func
                self.assignable = False
                return
            errors.error("Entity not found.", line=rhs.position)

        if not lhs.ret_type.has_members or lhs.ret_type.get_member_info(lhs, rhs) is None:
            # get function if struct doesn't contain members.
            # global functions can still use the member access syntax on structs
            # possible_func = self._get_global_func(func.module, rhs.var_name)
            possible_func = rhs.get_var(func)
            if possible_func is not None:
                self.ret_type = possible_func
                self.assignable = False
            elif lhs.ret_type.has_members:
                errors.error("Member not found!", line=rhs.position)
            else:
                errors.error("Has no members", line=self.position)
        else:
            super().pre_eval_math(func)
            member_info = lhs.ret_type.get_member_info(lhs, rhs)
            self.assignable = member_info.mutable
            self.is_pointer = member_info.is_pointer
            self.ret_type = member_info.typ

    def _get_global_func(self, module, name: str):
        value = module.get_global(name)
        if value is None:
            return None
        return value.obj

    def get_coupled_lifetimes(self, func) -> list:
        return self.lhs.get_coupled_lifetimes(func)

    def get_ptr(self, func):
        from Ast.nodes.container import ContainerNode

        lhs = self.lhs
        rhs = self.rhs
        if isinstance(rhs, ContainerNode):
            possible_func = rhs.children[0].get_var(func)
            if possible_func is not None:
                return
            errors.error("Entity not found.", line=rhs.position)

        if not lhs.ret_type.has_members or lhs.ret_type.get_member_info(lhs, rhs) is None:
            possible_func = rhs.get_var(func)

            if possible_func is not None:
                return possible_func
            errors.error("Has no members", line=self.position)

        return (lhs.ret_type).get_member(func, lhs, rhs)

    def get_var(self, func):
        self.ptr = self.get_ptr(func)
        return self

    def get_lifetime(self, func):
        return self.lhs.get_lifetime(func)

    def using_global(self, func) -> bool:
        from Ast.nodes.container import ContainerNode
        rhs = self.rhs
        lhs = self.lhs

        if isinstance(rhs, ContainerNode):
            return True

        possible_func = rhs.get_var(func)
        return (possible_func is not None and (not lhs.ret_type.has_members or lhs.ret_type.get_member_info(lhs, rhs) is None))

    def get_position(self) -> SrcPosition:
        return self.merge_pos((self.lhs.position,
                               self.rhs.position))


@operator(13, "access_member", pre_eval_right=False, cls=MemberAccess)
def member_access(self, func, lhs, rhs):
    ptr = self.get_ptr(func)
    if self.is_pointer:  # from llvmlite.ir.Type
        return func.builder.load(ptr)
    else:
        return ptr

# @operator(13, "index", cls = VariableIndexRef)
# def index(self, func, lhs, rhs):
#     pass

# @operator(11, "ref", cls=Ref)
# def ref(self, func, lhs, rhs):
#     pass


@operator(10, "as", pre_eval_right=False)
def _as(self, func, lhs, rhs):
    out = (lhs.ret_type).convert_to(func, lhs, rhs.as_type_reference(func))
    return out


# TODO: get this working (it seems llvm doesn't have a basic `pow` operation)
@operator(9, "Pow")
def pow(self, func, lhs, rhs):
    return (lhs.ret_type).pow(func, lhs, rhs)


@operator(8, "bitnot")
def bnot(self, func, lhs, rhs):
    return (lhs.ret_type).bit_not(func, lhs, rhs)


@operator(0, "Lshift")
def lshift(self, func, lhs, rhs):
    return (lhs.ret_type).lshift(func, lhs, rhs)


@operator(0, "Rshift")
def rshift(self, func, lhs, rhs):
    return (lhs.ret_type).rshift(func, lhs, rhs)


@operator(-1, "Band")
def band(self, func, lhs, rhs):
    return (lhs.ret_type).bit_and(func, lhs, rhs)


@operator(-2, "Bxor")
def bxor(self, func, lhs, rhs):
    return (lhs.ret_type).bit_xor(func, lhs, rhs)


@operator(-3, "Bor")
def bor(self, func, lhs, rhs):
    return (lhs.ret_type).bit_or(func, lhs, rhs)


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


@operator(-4, "eq")
def eq(self, func, lhs, rhs):
    return (lhs.ret_type).eq(func, lhs, rhs)


@operator(-4, "neq")
def neq(self, func, lhs, rhs):
    return (lhs.ret_type).neq(func, lhs, rhs)


@operator(-4, "le")
def le(self, func, lhs, rhs):
    return (lhs.ret_type).le(func, lhs, rhs)


@operator(-4, "leq")
def leq(self, func, lhs, rhs):
    return (lhs.ret_type).leq(func, lhs, rhs)


@operator(-4, "gr")
def gr(self, func, lhs, rhs):
    return (lhs.ret_type).gr(func, lhs, rhs)


@operator(-4, "geq")
def geq(self, func, lhs, rhs):
    return (lhs.ret_type).geq(func, lhs, rhs)

# * boolean ops


@operator(-7, "or")
def _or(self, func, lhs, rhs):
    return (lhs.ret_type)._or(func, lhs, rhs)


@operator(-6, "and")
def _and(self, func, lhs, rhs):
    return (lhs.ret_type)._and(func, lhs, rhs)


@operator(-5, "not")
def _not(self, func, lhs, rhs):
    return (lhs.ret_type)._not(func, lhs)

# * Inplace ops (-100 as precedence so that it is ALWAYS the last operation)


def check_valid_inplace(lhs) -> bool:
    '''check if lhs is a variable ref'''
    return lhs.assignable or \
        errors.error("Left-hand-side of inplace operation must be assignable!",
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
