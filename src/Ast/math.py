from collections import deque
from dataclasses import dataclass
from typing import Callable, NamedTuple

from llvmlite import ir

from Ast import Ast_Types
from Ast.nodetypes import NodeTypes

from .nodes import *

ops = {

}

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

    def pre_eval(self):
        self.lhs.pre_eval()
        self.rhs.pre_eval()

        self.ret_type = (self.lhs.ret_type).get_op_return(self.op_type, self.lhs, self.rhs)
        if self.ret_type == None: Ast_Types.AbstractType.print_error(self.op_type, self.lhs, self.rhs)
        self.ir_type = self.ret_type.ir_type
    
    def eval_math(self, func, lhs, rhs):
        return self.op.function(self, func, lhs, rhs)

    def eval(self, func):
        if not self.shunted:
            return shunt(self).eval(func) # type: ignore
        else:
            self.pre_eval()
            # * do conversions on args
            return self.eval_math(func, self.lhs, self.rhs)
        
    def __repr__(self) -> str:
        return f"<OperationNode `{self.lhs}` `{self.op.name}` `{self.rhs}`>"


# To any future programmers:
#   I am sorry for this shunt() function.
def shunt(node: OperationNode, op_stack = None, output_queue = None, has_parent=False) -> OperationNode|None:
    '''shunt Expressions to rearrange them based on the Order of Operations'''

    # * create stack and queue
    if op_stack == None:
        op_stack = deque()
    if output_queue==None:
        output_queue = []
    

    # * shunt thru the AST
    input_list = [node.lhs, node, node.rhs] # node: R,M,L
    for item in input_list:
        if type(item)==list: print(item[0].position, item[0])
        if not item.is_operator:
            output_queue.append(item)
        if item.is_operator:
            if item != node:
                shunt(item, op_stack, output_queue, True)
            if item == node:
                while len(op_stack) > 0:
                    x = op_stack.pop()
                    if x[1] > item.operator_precendence:
                        output_queue.append(x[0])
                    else:
                        op_stack.append(x)
                        break
                op_stack.append([item.op_type,item.operator_precendence])
    
    # * push remaining operators to Queue
    while (not has_parent) and len(op_stack) > 0:
        output_queue.append(op_stack.pop()[0])

    # * Create new Expression AST from output Queue
    while (not has_parent) and len(output_queue) > 1:
        stack = deque()
        for c,x in enumerate(output_queue):
            if isinstance(x, str):
                r,l = stack.pop(), stack.pop()
                
                p = ops[x]((-1,-1, -1), l[0],r[0], True)
    
                output_queue.pop(c)
                output_queue.pop(r[1])
                output_queue.pop(l[1])
                output_queue.insert(c-2, p)
                break
            else:
                stack.append([x,c])
    

    if (not has_parent):
        return output_queue[0]

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


@operator(-3, "or")
def _or(self, func, lhs, rhs):
    return (lhs.ret_type)._or(func, lhs, rhs)

@operator(-2, "and")
def _and(self, func, lhs, rhs):
    return (lhs.ret_type)._and(func, lhs, rhs)

@operator(-1, "not")
def _not(self, func, lhs, rhs):
    return (rhs.ret_type)._not(func, lhs, rhs)
