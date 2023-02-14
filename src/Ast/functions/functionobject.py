from typing import Any, Callable, Optional

from llvmlite import ir  # type: ignore

import errors
from Ast import Ast_Types

functionsdict: dict[str, dict[tuple[Ast_Types.Type, ...], '_Function']] = {}

internal_function_ty = Callable[[Any, tuple], Optional[ir.Instruction]]


# TODO: REMOVE FOR REAL FUNCTION TYPE
class _Function:
    '''A function object to run "interal functions" and "defined functions"'''
    __slots__ = ('function_behavior', 'function_object', 'ret_type',
                 'arg_types', 'name')

    # constants to be used to define behaviors
    BEHAVIOR_INTERNAL = 0
    BEHAVIOR_DEFINED = 1   # this is the default behavior if ``behavior >= 1``

    def __init__(self, behavior: int, name: str,
                 function_obj: internal_function_ty | ir.Function,
                 ret_type: Any, arg_types: tuple):
        self.function_behavior = behavior
        self.function_object = function_obj
        self.ret_type = ret_type
        self.arg_types = arg_types
        self.name = name

    def __str__(self):
        '''Example: my_func(int, int)'''
        return f'{self.name}({", ".join(self.arg_types)})'

    def call(self, func, args: tuple) -> Optional[ir.Instruction]:
        '''Call function'''
        if self.function_behavior:  # behavior != 0
            return func.builder.call(self.function_object, args)
        return self.function_object(func, args)  # type: ignore

    def get_ir_types(self):
        ir_types = []
        for arg in self.arg_types:
            if arg.pass_as_ptr:
                ir_types.append(arg.ir_type.as_pointer())
            else:
                ir_types.append(arg.ir_type)
        return tuple(ir_types)

    def declare(self, module):
        if self.function_behavior == self.BEHAVIOR_INTERNAL:
            return
        fnty = ir.FunctionType((self.ret_type).ir_type, self.get_ir_types(),
                               False)
        ir.Function(module.module, fnty,
                    name=module.get_unique_name(self.name))


def internal_function(name: str, ret_type: Any,
                      arg_types: tuple, *,
                      container=None):
    '''decorator to create internal functions'''
    if container is None:
        container = functionsdict

    def wrapper(func):
        if name not in container:
            container[name] = {}
        container[name][arg_types] = \
            _Function(_Function.BEHAVIOR_INTERNAL, name, func,
                      ret_type, arg_types)

        def call(ast_func, args: tuple) -> Optional[ir.Instruction]:
            # warning does not display in `_Function(...).call(...)`
            errors.developer_warning(
                "You should not call internal " +
                "functions via python __call__ convention.\ntip: " +
                "@internal_function indicates use inside of BCL code"
            )
            return func(ast_func, args)

        return call

    return wrapper
