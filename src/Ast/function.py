'''All AST nodes related to functions.'''
from ast import Module
from typing import Any, Callable, Optional

import errors
from llvmlite import ir

from Ast.literals import TypeRefLiteral
from Ast.nodetypes import NodeTypes
from Ast.varobject import VariableObj

from . import Ast_Types
from .nodes import (ASTNode, Block, ExpressionNode, KeyValuePair, ParenthBlock,
                    SrcPosition)

functions: dict[str, dict[tuple[Ast_Types.Type, ...], '_Function']] = {}


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
    def args_ir(self) -> tuple[ir.Type, ...]:
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

    def __init__(self, pos: SrcPosition, name: str, args: ParenthBlock, block: Block, module: Module):
        self._position   = pos
        self.func_name   = name
        self.ret_type: Ast_Types.Type|TypeRefLiteral = Ast_Types.Void() # Can also be a TypeRef. In which case, it should be evaled

        self.builder     = None # llvmlite.ir.IRBuilder object once created
        self.block       = block  # body of the function Ast.Block
        self.module      = module # Module the object is contained in
        self.is_ret_set  = False  # is the return value set?
        self.has_return  = False  # Not to be confused with "is_ret_set", this is used for ensuring that a `return` always accessible
        self.inside_loop = None   # Whether or not the IRBuilder is currently inside a loop block, set to the loop node
        self.ir_entry    = None   # Entry section of the function. Used when declaring "invisible" variables
        self.variables: list[tuple] = []
        self.consts: list[tuple] = []

        self._validate_args(args) # validate arguments

        # construct args lists
        self.args: dict[str, ExpressionNode] = dict()
        self.args_ir: tuple[ir.Type, ...] = () # list of all the args' ir types
        self.args_types: tuple[Ast_Types.Type, ...] = () # list of all the args' Ast_Types.Type return types
        self._construct_args(args)
        
    
    def _construct_args(self, args: ParenthBlock):
        '''Construct the lists of args required when building this function'''
        args_ir    = []
        args_types = []
        for arg in args:
            self.args[arg.key] = [None, arg.value, True] #type: ignore
            if arg.get_type().pass_as_ptr:
                args_ir.append(arg.get_type().ir_type.as_pointer())
            else:
                args_ir.append(arg.get_type().ir_type)
            args_types.append(arg.get_type())
        
        self.args_ir = tuple(args_ir)
        self.args_types = tuple(args_types)


    def _validate_args(self, args: ParenthBlock):
        '''Validate that all args are syntactically valid'''
        if not args.is_key_value_pairs():
            errors.error(f"Function {self.func_name}'s argument tuple consists of non KV_pairs", line = self.position)

    def _validate_return(self):
        ret_line = (-1,-1,-1)
        if self.is_ret_set:
            self.ret_type.eval(self)
            ret_line = self.ret_type.position
            self.ret_type = self.ret_type.ret_type
        if self.ret_type.name == "ref":
            errors.error(f"Function {self.func_name} cannot return a reference to a local variable or value.", line = ret_line)

    def _mangle_name(self, name) -> str:
        '''add an ID to the end of a name if the function has a body and is NOT named "main"'''
        return self.module.get_unique_name(name)

    def _append_args(self):
        '''append all args as variables usable inside the function body'''
        args = self.function_ir.args
        for c,x in enumerate(self.args.keys()):
            self.block.variables[x].ptr = args[c]
            self.variables.append((self.block.variables[x], x))
    
    def pre_eval(self):
        global functions

        self._validate_return()
        fnty = ir.FunctionType((self.ret_type).ir_type, self.args_ir, False)

        if self.func_name not in functions:
            functions[self.func_name] = dict()


        self.function_ir = ir.Function(self.module.module, fnty, name=self._mangle_name(self.func_name))
        functions[self.func_name][self.args_types] = _Function(_Function.BEHAVIOR_DEFINED,
                                                          self.func_name, self.function_ir,
                                                          self.ret_type, self.args_types) 
        # Early return if the function has no body.
        if self.block is None:
            return

        block = self.function_ir.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)
        self.ir_entry = block
        self._append_args()

    def create_const_var(self, typ):
        current_block = self.builder.block
        self.builder.position_at_start(self.ir_entry)
        ptr = self.builder.alloca(typ.ir_type, name = self._mangle_name("CONST"))
        self.builder.position_at_end(current_block)
        return ptr

    def alloc_stack(self):
        for x in self.variables:
            if x[0].is_constant:
                if x[0].type.pass_as_ptr:
                    val = self.builder.load(x[0].ptr)
                else:
                    val = x[0].ptr
                if not x[0].type.no_load:
                    ptr = self.builder.alloca(x[0].type.ir_type)
                    self.builder.store(val, ptr)
                    x[0].ptr = ptr
                x[0].is_constant = False
                continue
            else:
                x[0].define(self, x[1])

    def eval(self):
        if self.block is None:
            return
        self.function_ir.attributes.add("nounwind")
        self.block.pre_eval(self)
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

    def __init__(self, pos: SrcPosition, expr: ExpressionNode):
        self._position = pos
        self.expr = expr

    def pre_eval(self, func):
        self.expr.pre_eval(func)

    def _check_valid_type(self, func):
        if self.expr.ret_type != func.ret_type:
            errors.error(f"Funtion, \"{func.func_name}\", has a return type of '{func.ret_type}'. \
                            Return statement returned '{self.expr.ret_type}'",
                            line = self.position)

    def eval(self, func):
        func.has_return = True
        self._check_valid_type(func)

        if func.ret_type.is_void():
            func.builder.ret_void()
        else:
            func.builder.ret(self.expr.eval(func))
class FunctionCall(ExpressionNode):
    '''Defines a function in the IR'''
    __slots__ = ('ir_type', 'paren', 'function', 'args_types', "func_name")
    name = "funcCall"
    
    def __init__(self, pos: SrcPosition,name: str, parenth: ParenthBlock):
        super().__init__(pos)
        self.func_name = name
        self.ret_type  = Ast_Types.Void()
        self.paren     = parenth
        
    
    def _check_function_exists(self):
        '''ensure a function exists and the correct form of it exists'''
        if self.func_name not in functions \
            or self.args_types not in functions[self.func_name]:
            args_for_error = ','.join([str(x) for x in self.args_types])
            errors.error(f"function '{self.func_name}({args_for_error})' was never defined", line = self.position)

    def pre_eval(self, func):
        if self.paren.name == "Parenth":
            self.paren.in_func_call = True
        self.paren.pre_eval(func)

        self.args_types = tuple([x.ret_type for x in self.paren])
        self._check_function_exists()
        
        self.ret_type = functions[self.func_name][self.args_types].ret_type
        self.ir_type = (self.ret_type).ir_type
        self.function = functions[self.func_name][self.args_types]
        
    
    def eval(self, func):
        x = self.paren.eval(func)
        if isinstance(self.paren, ParenthBlock):
            args = self.paren.children
        else:
            args = [x]
        return self.function.call(func, args)
