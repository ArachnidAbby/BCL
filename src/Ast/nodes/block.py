from collections import deque
from typing import Any, Iterator, Self

from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.container import ContainerNode


class Block(ContainerNode):
    '''Provides a Block node that contains other `AST_NODE` objects'''
    __slots__ = ('variables', 'builder', 'last_instruction', 'ended', 'parent')

    BLOCK_STACK: deque[Self] = deque()

    def __init__(self, pos: SrcPosition, parent=None, *args, **kwargs):
        super().__init__(pos, *args, **kwargs)
        self.variables: dict[str, object] = {}
        # {name: VarObj, ...} -- recursive import uppon proper type annotation
        self.builder = None
        self.last_instruction = False
        self.ended = False
        self.parent = parent

    def append_nested_vars(self):
        '''append vars for nested blocks'''
        if len(self.BLOCK_STACK) != 0:
            self.variables = {**self.variables,
                              **self.BLOCK_STACK[-1].variables}

    def pre_eval(self, func):
        # self.append_nested_vars()
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
        self.BLOCK_STACK.append(self)  # type: ignore
        for child in self.children[0:-1]:
            yield child
            if self.ended:
                self.BLOCK_STACK.pop()
                return
        yield self.children[-1]
        self.BLOCK_STACK.pop()

    def get_variable(self, var_name: str):
        '''get variable by name'''
        if var_name in self.variables.keys():
            return self.variables[var_name]
        elif self.parent is not None:
            return self.parent.get_variable(var_name)
        else:
            return None

    def validate_variable(self, var_name: str) -> bool:
        '''Return true if a variable already has a ptr'''
        var_ptr = self.get_variable(var_name).ptr  # type: ignore
        return var_ptr is not None

    def validate_variable_exists(self, var_name: str) -> bool:
        if self.parent is None:
            return var_name in self.variables.keys()
        return (var_name in self.variables.keys()) or \
            self.parent.validate_variable_exists(var_name)

    def repr_as_tree(self) -> str:
        return self.create_tree("Block",
                                contents=self.children,
                                variables=self.variables)
