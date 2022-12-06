from collections import deque
from typing import Callable, NamedTuple

import errors
from llvmlite import ir

from .nodes import *

ops = dict()

class Operation(NamedTuple):
    operator_precendence: int
    name: str
    function: Callable[[ASTNode, ASTNode, Any, Any], ir.Instruction|None]

    def __call__(self, pos, lhs, rhs, shunted=False):
        return OperationNode(pos, self, lhs, rhs, shunted)

class OperationNode(ExpressionNode):
    '''Operation class to define common behavior in Operations'''
    __slots__ = ("op", "shunted", "lhs", "rhs")
    is_operator = True

    def init(self, op, lhs, rhs, shunted = False):
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

    def pre_eval(self, func):
        self.lhs.pre_eval(func)
        self.rhs.pre_eval(func)
        
        # print(self.lhs.ret_type, self)
        self.ret_type = (self.lhs.ret_type).get_op_return(self.op_type, self.lhs, self.rhs)
        if self.ret_type!=None:
            self.ir_type = self.ret_type.ir_type
        # print(self.lhs.ret_type, self)
    
    def eval_math(self, func, lhs, rhs):
        return self.op.function(self, func, lhs, rhs)

    def eval(self, func):
        if not self.shunted:
            return RPN_to_node(shunt(self)).eval(func)
        else:
            self.pre_eval(func)
            return self.eval_math(func, self.lhs, self.rhs)
    
    def __str__(self) -> str:
        return f"<{str(self.lhs)} |{self.op.name}| {str(self.rhs)}>"

# To any future programmers:
#   I am sorry for this shunt() function.
def shunt(node: OperationNode) -> deque:
    # * create stack and queue
    
    op_stack = deque()
    output_queue = deque()
    
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
                    if op[1] >= item.operator_precendence:
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

    op_stack = deque()

    while len(shunted_data) > 1:
        stack = deque()
        for c,x in enumerate(shunted_data):
            if isinstance(x, str):
                r,l = stack.pop(), stack.pop()
                
                p = ops[x](l[0].position, l[0],r[0], True)
    
                del shunted_data[c]
                del shunted_data[r[1]]
                del shunted_data[l[1]]

                shunted_data.insert(c-2, p)
                break
            else:
                stack.append((x,c))
    

    return shunted_data[0]

def operator(precedence: int, name: str):
    def wrapper(func):
        global ops
        op = Operation(precedence, name.lower(), func)
        ops[name.upper()] = op
        ops[name.lower()] = op

        def new_func(self, pos, lhs, rhs, shunted=False):
            '''changes the original function into a factory/generator for OperationNode(pos, op, ...)'''
            return op(pos, lhs, rhs, shunted)

        return new_func
    return wrapper

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
    return lhs.name == "varRef" or \
      errors.error("Left-hand-side of inplace operation must be a variable!", line = lhs.position) # only runs if false!

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
