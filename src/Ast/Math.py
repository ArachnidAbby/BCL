from collections import deque

from llvmlite import ir

from . import Types
from .Nodes import *
class Operation(AST_NODE):
    '''Operation class to define common behavior in Operations'''
    __slots__ = ["ir_type", "operator_precendence", "op_type", "shunted"]

    def pre_eval(self):
        self.children[0].pre_eval()
        self.children[1].pre_eval()

        self.ret_type = Types.types[self.children[0].ret_type].get_op_return(self.op_type, self.children[0], self.children[1])
        self.ir_type = Types.types[self.ret_type].ir_type

        # print(self.ret_type)
    
    def eval_math(self, func, lhs, rhs):
        pass

    def eval(self, func):
        if not self.shunted:
            return shunt(self).eval(func)
        else:
            self.pre_eval()
            # * do conversions on args
            # lhs = Types.types[self.ret_type].convert_from(func,self.children[0].ret_type, self.children[0].eval(func))
            # rhs = Types.types[self.ret_type].convert_from(func,self.children[1].ret_type, self.children[1].eval(func))
            lhs = self.children[0]
            rhs = self.children[1]
            return self.eval_math(func, lhs, rhs)


def shunt(node: AST_NODE, op_stack = None, output_queue = None, has_parent=False) -> Operation|None:
    '''shunt Expressions to rearrange them based on the Order of Operations'''

    # * create stack and queue
    if op_stack == None:
        op_stack = deque()
    if output_queue==None:
        output_queue = []
    

    # * shunt thru the AST
    input_list = [node.children[0], node, node.children[1]] # node: R,M,L
    for item in input_list:
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
    while (not has_parent) and len(op_stack)>0:
        output_queue.append(op_stack.pop()[0])

    # * Create new Expression AST from output Queue
    while (not has_parent) and len(output_queue) > 1:
        stack = deque()
        for c,x in enumerate(output_queue):
            if isinstance(x, str):
                r,l = stack.pop(), stack.pop()
                
                p = ops[x]((-1,-1, -1), [l[0],r[0]], True)
    
                output_queue.pop(c)
                output_queue.pop(r[1])
                output_queue.pop(l[1])
                output_queue.insert(c-2, p)
                break
            else:
                stack.append([x,c])
    

    if (not has_parent):return output_queue[0]

class Sum(Operation):
    '''Basic sum operation. It acts as an `expr`'''
    __slots__ = ["ir_type", "operator_precendence", "op_type", "shunted"]

    def init(self, shunted = False):
        self.shunted = shunted

        self.is_operator = True
        self.op_type = "sum"
        self.operator_precendence = 1
    
    def eval_math(self, func, lhs, rhs):
        return Types.types[lhs.ret_type].sum(func,lhs,rhs)

class Sub(Operation):
    '''Basic sub operation. It acts as an `expr`'''
    __slots__ = ["ir_type", "operator_precendence", "op_type", "shunted"]
    
    def init(self, shunted = False):
        self.shunted = shunted

        self.is_operator = True
        self.op_type = "sub"
        self.operator_precendence = 1

    def eval_math(self, func, lhs, rhs):
        return Types.types[lhs.ret_type].sub(func,lhs,rhs)

class Mul(Operation):
    '''Basic Mul operation. It acts as an `expr`'''
    __slots__ = ["ir_type", "operator_precendence", "op_type", "shunted"]
    
    def init(self, shunted = False):
        self.shunted = shunted
        self.is_operator = True
        self.op_type = "mul"
        self.operator_precendence = 2

    def eval_math(self, func, lhs, rhs):
        return Types.types[lhs.ret_type].mul(func,lhs,rhs)

class Div(Operation):
    '''Basic Div operation. It acts as an `expr`'''
    __slots__ = ["ir_type", "operator_precendence", "op_type", "shunted"]
    
    def init(self, shunted = False):
        self.shunted = shunted
        self.is_operator = True
        self.op_type = "div"
        self.operator_precendence = 2

    def eval_math(self, func, lhs, rhs):
        return Types.types[lhs.ret_type].div(func,lhs,rhs)

class Mod(Operation):
    '''Basic Mod operation. It acts as an `expr`'''
    __slots__ = ["ir_type", "operator_precendence", "op_type", "shunted"]
    
    def init(self, shunted = False):
        self.shunted = shunted
        self.is_operator = True
        self.op_type = "mod"
        self.operator_precendence = 2

    def eval_math(self, func, lhs, rhs):
        return Types.types[lhs.ret_type].mod(func,lhs,rhs)

class Comparators(Operation):
    '''Basic Eq operation. It acts as an `expr`'''
    __slots__ = ["ir_type", "operator_precendence", "op_type", "shunted", "op_name"]
    
    def __init__(self, op_name, run_super = False, *args, **kwargs):
        self.op_name = op_name
        if run_super:
            super().__init__(*args, **kwargs)

    def init(self, shunted = False):
        self.shunted = shunted
        self.is_operator = True
        self.op_type = self.op_name
        self.operator_precendence = 0
    
    def __call__(self, pos, children, *args, **kwargs):
        return Comparators(self.op_name, True, *([pos, children] + list(args)), **kwargs)

    # def pre_eval(self, revert_type = True):
    #     super().pre_eval()
    #     if revert_type:
    #         self.ret_type = 'bool'
    #         self.ir_type = Types.Integer_1.ir_type
        
    def eval_math(self, func, lhs, rhs):
        # * do conversions on args
        # self.pre_eval(revert_type = False)
        # lhs = Types.types[self.ret_type].convert_from(func,self.children[0].ret_type, self.children[0].eval(func))
        # rhs = Types.types[self.ret_type].convert_from(func,self.children[1].ret_type, self.children[1].eval(func))
        match self.op_name:
            case 'eq':
                return Types.types[lhs.ret_type].eq(func,lhs,rhs)
            case 'neq':
                return Types.types[lhs.ret_type].neq(func,lhs,rhs)
            case 'geq':
                return Types.types[lhs.ret_type].geq(func,lhs,rhs)
            case 'leq':
                return Types.types[lhs.ret_type].leq(func,lhs,rhs)
            case 'le':
                return Types.types[lhs.ret_type].le(func,lhs,rhs)
            case 'gr':
                return Types.types[lhs.ret_type].gr(func,lhs,rhs)


ops = {
    "sum": Sum,
    "SUM": Sum,
    "sub": Sub,
    "SUB": Sub,
    "mul": Mul,
    "MUL": Mul,
    "div": Div,
    "DIV": Div,
    "mod": Mod,
    "MOD": Mod,
    "eq": Comparators('eq'),
    "EQ": Comparators('eq'),
    "neq": Comparators('neq'),
    "NEQ": Comparators('neq'),
    "geq": Comparators('geq'),
    "GEQ": Comparators('geq'),
    "leq": Comparators('leq'),
    "LEQ": Comparators('leq'),
    "le": Comparators('le'),
    "LE": Comparators('le'),
    "gr": Comparators('gr'),
    "GR": Comparators('gr'),
}
