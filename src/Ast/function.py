'''All AST nodes related to functions.'''
from ast import Module
from typing import Any, Callable, Optional

from llvmlite import ir

import errors
from Ast.literals import TypeRefLiteral
from Ast.nodetypes import NodeTypes
from Ast.variables.varobject import VariableObj

from . import Ast_Types
from .nodes import (ASTNode, Block, ExpressionNode, KeyValuePair, ParenthBlock,
                    SrcPosition)

functions: dict[str, dict[tuple[Ast_Types.Type, ...], '_Function']] = {}


# TODO: REMOVE FOR REAL FUNCTION TYPE
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






