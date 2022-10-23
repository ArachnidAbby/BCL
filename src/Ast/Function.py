from typing import Any, Callable, Optional

import Errors
from llvmlite import ir

from Ast.Ast_Types.Type_Base import types_dict
from Ast.Node_Types import NodeTypes

from . import Ast_Types
from .Nodes import ASTNode, Block, ExpressionNode, ParenthBlock

functions = {}


class _Function:
    '''A function object to run "interal functions" and "defined functions"'''
    __slots__ = ('function_behavior', 'function_object', 'ret_type', 'arg_types', 'name')


    # constants to be used to define behaviors
    BEHAVIOR_INTERNAL = 0
    BEHAVIOR_DEFINED  = 1   # this is the default behavior if ``behavior >= 1``

    def __init__(self, behavior: int, name: str, 
                 function_obj: Callable[[Any, tuple], Optional[ir.Instruction]] | ir.Function,
                 ret_type: Any, arg_types: tuple):
        self.function_behavior = behavior
        self.function_object   = function_obj
        self.ret_type          = ret_type
        self.arg_types         = arg_types
        self.name              = name

    def __str__(self):
        '''Example: my_func(int, int)'''
        return f'{self.name}({", ".join(self.arg_types)})'

    @property
    def args_ir(self) -> tuple[ir.Type]:
        '''Get the `ir.Type` of all args'''
        return tuple([x.ir_type for x in self.arg_types])

    def call(self, func, args: tuple) -> Optional[ir.Instruction]:
        '''Call function'''
        if self.function_behavior: # behavior != 0
            return func.builder.call(self.function_object, args)
        # else
        return self.function_object(func, args)  # type: ignore


def internal_function(name: str, ret_type: Any,
                      arg_types: tuple, *,
                      container=functions):
    '''decorator to create internal functions'''
    def wrapper(func):
        if name not in container:
            container[name] = dict()
        container[name][arg_types] = _Function(_Function.BEHAVIOR_INTERNAL, name, func, ret_type, arg_types)

        def call(ast_func, args: tuple) -> Optional[ir.Instruction]:
            # warning does not display in `_Function(...).call(...)`
            Errors.developer_warning("You should not call internal functions via python __call__ convention.\
                                      \ntip: @internal_function indicates use inside of BCL code")
            return func(ast_func, args)

        return call

    return wrapper

# *example
# @internal_function("jo_jo_reference", Integer32, tuple())
# def test(func, args):
#     return None

# test(0,0) # throws a warning at runtime
# print(functions)
# functions["jo_jo_reference"][tuple()].call(0,(0,)) # no warnings

class FunctionDef(ASTNode):
    '''Defines a function in the IR'''
    __slots__ = ('builder', 'block', 'function_ir', 'args', 'args_ir', 'module','is_ret_set', 'args_types', 'ret_type')
    
    def init(self, name: str, args: ParenthBlock, block: Block, module):
        self.name = name
        self.type = NodeTypes.STATEMENT
        self.ret_type = Ast_Types.Void()

        self.builder = None
        self.block = block
        self.module = module
        self.is_ret_set = False

        self._validate(args) # validate arguments

        # construct args lists
        self.args = dict()
        self.args_ir = list()
        self.args_types = list()

        for arg in args:
            self.args[arg.key] = [None, arg.value, True]
            self.args_ir.append(arg.get_type().ir_type)
            self.args_types.append(arg.get_type())
        
        self.args_ir = tuple(self.args_ir)
        self.args_types = tuple(self.args_types)

    def _validate(self, args):
        '''Validate that all args are syntactically valid'''
        if not args.is_key_value_pairs():
            Errors.error(f"Function {self.name}'s argument tuple consists of non KV_pairs", line = self.position)

        for x in args:
            if not x.keywords:
                Errors.error(f"Function {self.name}'s argument tuple can only consist of Keyword pairs\
                               \n\t invalid pair \
                               '{x.key}: {x.value}'", 
                               line = self.position)

    def pre_eval(self):
        fnty = ir.FunctionType((self.ret_type).ir_type, self.args_ir, False)

        self.function_ir = ir.Function(self.module, fnty, name=self.name)
        
        global functions
        
        if self.name not in functions:
            functions[self.name] = dict()
        functions[self.name][self.args_types] = _Function(_Function.BEHAVIOR_DEFINED,
                                                          self.name, self.function_ir,
                                                          self.ret_type, self.args_types) # type: ignore

    def eval(self):
        self.block.pre_eval()
        block = self.function_ir.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)

        args = self.function_ir.args
        
        # * add variables into block
        for c,x in enumerate(self.args.keys()):
            self.block.variables[x].ptr = args[c]
        
        self.block.eval(self)
        
        if self.ret_type.name == 'void':
            self.builder.ret_void()

class ReturnStatement(ASTNode):
    __slots__ = ('expr')

    def init(self, expr):
        self.name = "return"
        self.type = NodeTypes.STATEMENT
        self.expr = expr

    def pre_eval(self):
        pass

    def eval(self, func):
        self.expr.pre_eval()
        if self.expr.ret_type != func.ret_type:
            Errors.error(
                f"Funtion, \"{func.name}\", has a return type of '{func.ret_type}'. Return statement returned '{self.expr.ret_type}'",
                line = self.position
            )

        if func.ret_type.name == 'void':
            func.builder.ret_void()
            return None

        func.builder.ret(self.expr.eval(func))
class FunctionCall(ExpressionNode):
    '''Defines a function in the IR'''
    __slots__ = ('ir_type', 'paren', 'function', 'args_types')
    
    def init(self, name: str, parenth: ParenthBlock):
        self.name = name
        self.ret_type = Ast_Types.Void()
        self.ir_type = None

        self.paren = parenth
    
    def pre_eval(self):
        self.paren.pre_eval()

        self.args_types = tuple([x.ret_type for x in self.paren])
        if self.name not in functions \
            or self.args_types not in functions[self.name]:
            Errors.error(f"function '{self.name}{self.args_types}' was never defined", line = self.position)
        
        self.ret_type = functions[self.name][self.args_types].ret_type
        self.ir_type = (self.ret_type).ir_type
        self.function = functions[self.name][self.args_types]
    
    def eval(self, func):
        x = self.paren.eval(func)
        args = self.paren.children if x==None else [x]
        
        return self.function.call(func, args)
