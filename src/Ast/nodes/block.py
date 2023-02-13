from collections import deque
from typing import Any, Iterator, Self

from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.container import ContainerNode


class Block(ContainerNode):
    '''Provides a Block node that contains other `AST_NODE` objects'''
    __slots__ = ('variables', 'builder', 'last_instruction', 'ended')

    # TODO: Move global state to centralized location
    BLOCK_STACK: deque[Self] = deque()

    def __init__(self, pos: SrcPosition, *args, **kwargs):
        super().__init__(pos, *args, **kwargs)
        self.variables: dict[str, object] = {}
        # {name: VarObj, ...} -- recursive import uppon proper type annotation
        self.builder = None
        self.last_instruction = False
        self.ended = False

    def append_nested_vars(self):
        '''append vars for nested blocks'''
        if len(self.BLOCK_STACK) != 0:
            self.variables = {**self.variables,
                              **self.BLOCK_STACK[-1].variables}

    def pre_eval(self, func):
        self.append_nested_vars()
        self.BLOCK_STACK.append(self)
        for x in self.children:
            x.pre_eval(func)
        self.BLOCK_STACK.pop()

    def eval(self, func):
        if len(self.children) == 0:
            self.last_instruction = not func.ret_type.is_void()
            return
        self.BLOCK_STACK.append(self)
        for x in self.children[0:-1]:
            x.eval(func)
            if func.has_return or self.ended:
                self.BLOCK_STACK.pop()
                return
        self.last_instruction = not func.ret_type.is_void()
        self.children[-1].eval(func)
        self.BLOCK_STACK.pop()

    def __iter__(self) -> Iterator[Any]:
        self.BLOCK_STACK.append(self)
        for child in self.children[0:-1]:
            yield child
            if self.ended:
                self.BLOCK_STACK.pop()
                return
        yield self.children[-1]
        self.BLOCK_STACK.pop()

    def get_variable(self, var_name: str):
        '''get variable by name'''
        return self.variables[var_name]

    def validate_variable(self, var_name: str) -> bool:
        '''Return true if a variable already has a ptr'''
        return self.variables[var_name].ptr is not None

    def validate_variable_exists(self, var_name: str) -> bool:
        return var_name in self.variables.keys()
