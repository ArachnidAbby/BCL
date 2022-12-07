'''All AST nodes related to functions.'''
from typing import Any, Callable, Optional

import errors
from llvmlite import ir

from Ast.nodetypes import NodeTypes
from Ast.varobject import VariableObj

from . import Ast_Types
from .nodes import ASTNode, Block, ExpressionNode, ParenthBlock

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
        return tuple([x.ir_type if x.ret_type.name!="array" else x.ir_type.as_pointer() for x in self.arg_types])

    def call(self, func, args: tuple) -> Optional[ir.Instruction]:
        '''Call function'''
        if self.function_behavior: # behavior != 0
            return func.builder.call(self.function_object, args)
        # else
        return self.function_object(func, args)  # type: ignore


def internal_function(name: str, ret_type: Any,
                      arg_types: tuple, *,
                      container=None):
    '''decorator to create internal functions'''
    if container is None:
        container = functions
    def wrapper(func):
        if name not in container:
            container[name] = {}
        container[name][arg_types] = \
            _Function(_Function.BEHAVIOR_INTERNAL, name, func, ret_type, arg_types)

        def call(ast_func, args: tuple) -> Optional[ir.Instruction]:
            # warning does not display in `_Function(...).call(...)`
            errors.developer_warning("You should not call internal functions \
                via python __call__ convention.\ntip: @internal_function indicates \
                use inside of BCL code")
            return func(ast_func, args)

        return call

    return wrapper


class FunctionDef(ASTNode):
    '''Defines a function in the IR'''
    __slots__ = ('builder', 'block', 'function_ir', 'args', 'args_ir', 'module','is_ret_set',
                'args_types', 'ret_type', "has_return", "inside_loop", "func_name", "variables", "consts",
                "ir_entry")
    type = NodeTypes.STATEMENT
    name = "funcDef"

    def init(self, name: str, args: ParenthBlock, block: Block, module):
        self.func_name = name
        self.ret_type = Ast_Types.Void()

        self.builder = None
        self.block = block
        self.module = module
        self.is_ret_set = False
        self.has_return = False
        self.inside_loop = None
        self.ir_entry = None
        self.variables: list[tuple] = []
        self.consts: list[tuple] = []

        self._validate(args) # validate arguments

        # construct args lists
        self.args = dict()
        self.args_ir = list()
        self.args_types = list()
        
        for arg in args:
            self.args[arg.key] = [None, arg.value, True]
            if arg.get_type().name == "array":
                self.args_ir.append(arg.get_type().ir_type.as_pointer())
            else:
                self.args_ir.append(arg.get_type().ir_type)
            self.args_types.append(arg.get_type())
        
        self.args_ir = tuple(self.args_ir)
        self.args_types = tuple(self.args_types)

    def _validate(self, args):
        '''Validate that all args are syntactically valid'''
        if not args.is_key_value_pairs():
            errors.error(f"Function {self.func_name}'s argument tuple consists of non KV_pairs", line = self.position)

        for x in args:
            if not x.keywords:
                errors.error(f"Function {self.func_name}'s argument tuple can only consist of Keyword pairs\
                               \n\t invalid pair:    '{x.key}: {x.value}'\n", 
                               line = self.position)

    def pre_eval(self):
        global functions

        if self.is_ret_set:
            self.ret_type.eval(self)
            self.ret_type = self.ret_type.ret_type
        fnty = ir.FunctionType((self.ret_type).ir_type, self.args_ir, False)

        if self.func_name not in functions:
            functions[self.func_name] = dict()

        # avoid name collisions by adding a # to the end of the function name
        if self.func_name!="main":
            name = f"{self.func_name}.{len(functions[self.func_name].keys())}"
        else:
            name = self.func_name 

        self.function_ir = ir.Function(self.module.module, fnty, name=name)
        
        functions[self.func_name][self.args_types] = _Function(_Function.BEHAVIOR_DEFINED,
                                                          self.func_name, self.function_ir,
                                                          self.ret_type, self.args_types) # type: ignore

    def create_const_var(self, typ):
        current_block = self.builder.block
        self.builder.position_at_start(self.ir_entry)
        ptr = self.builder.alloca(typ.ir_type, name = f"--CONST-")
        self.builder.position_at_end(current_block)
        return ptr

    def alloc_stack(self):
        args = self.function_ir.args
        for c,x in enumerate(self.args.keys()):
            self.block.variables[x].ptr = args[c]
            self.variables.append((self.block.variables[x], x))

        for x in self.variables:
            if x[0].is_constant:
                if x[0].type.pass_as_ptr:
                    val = self.builder.load(x[0].ptr)
                else:
                    val = x[0].ptr
                ptr = self.builder.alloca(x[0].type.ir_type)
                self.builder.store(val, ptr)
                x[0].ptr = ptr
                x[0].is_constant = False
                continue
            else:
                x[0].define(self, x[1])

    def eval(self):
        self.block.pre_eval(self)
        block = self.function_ir.append_basic_block("entry")
        self.ir_entry =block 
        self.builder = ir.IRBuilder(block)
        self.function_ir.attributes.add("nounwind")
        self.alloc_stack()

        args = self.function_ir.args
        
        self.block.eval(self)
        
        if self.ret_type.is_void():
            self.builder.ret_void()
        elif not self.has_return:
            errors.error(f"Function '{self.func_name}' has no guaranteed return! Ensure that at least 1 return statement is reachable!")

class ReturnStatement(ASTNode):
    __slots__ = ('expr')
    type = NodeTypes.STATEMENT
    name = "return"

    def init(self, expr):
        self.expr = expr

    def pre_eval(self, func):
        pass

    def eval(self, func):
        self.expr.pre_eval(func)
        func.has_return = True
        if self.expr.ret_type != func.ret_type:
            errors.error(
                f"Funtion, \"{func.func_name}\", has a return type of '{func.ret_type}'. Return statement returned '{self.expr.ret_type}'",
                line = self.position
            )

        if func.ret_type.is_void():
            func.builder.ret_void()
            return None
        func.builder.ret(self.expr.eval(func))
class FunctionCall(ExpressionNode):
    '''Defines a function in the IR'''
    __slots__ = ('ir_type', 'paren', 'function', 'args_types', "func_name")
    name = "funcCall"
    
    def init(self, name: str, parenth: ParenthBlock):
        self.func_name = name
        self.ret_type = Ast_Types.Void()

        self.paren = parenth
    
    def pre_eval(self, func):
        if self.paren.name == "Parenth":
            self.paren.in_func_call = True
        self.paren.pre_eval(func)

        self.args_types = tuple([x.ret_type for x in self.paren])
        if self.func_name not in functions \
            or self.args_types not in functions[self.func_name]:
            args_for_error = ','.join([str(x) for x in self.args_types])
            errors.error(f"function '{self.func_name}({args_for_error})' was never defined", line = self.position)
        
        self.ret_type = functions[self.func_name][self.args_types].ret_type
        self.ir_type = (self.ret_type).ir_type
        self.function = functions[self.func_name][self.args_types]
        
    
    def eval(self, func):
        x = self.paren.eval(func)
        if x==None:
            args = self.paren.children
        else:
            args = [x]
        args = self.paren.children  
        
        return self.function.call(func, args)
