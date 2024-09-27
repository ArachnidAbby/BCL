from collections import deque
from typing import TYPE_CHECKING, Any, Iterator, Self

from llvmlite import ir

from Ast.nodes.commontypes import SrcPosition
from Ast.nodes.container import ContainerNode

if TYPE_CHECKING:
    from Ast.variables.varobject import VariableObj


class Block(ContainerNode):
    '''Provides a Block node that contains other `AST_NODE` objects'''
    __slots__ = ('variables', 'builder', 'last_instruction', 'ended', 'parent',
                 'module', 'constants', 'dispose_queue')

    BLOCK_STACK: deque[Self] = deque()

    def __init__(self, pos: SrcPosition, parent=None, module=None):
        super().__init__(pos)
        self.variables: dict[str, "VariableObj"] = {}
        # {name: varobj, ...} -- recursive import uppon proper type annotation
        self.builder = None
        self.last_instruction = False
        self.ended = False
        self.parent = parent
        self.module = module
        # Constants allocated here.
        self.constants = []
        self.dispose_queue = []

    def simple_copy(self):
        out = Block(self._position, module=self.module)
        out.children = [child.copy() for child in self.children if child is not None]
        return out

    def copy(self):
        out = Block(self._position, module=self.module)
        if len(self.BLOCK_STACK) != 0:
            out.parent = self.BLOCK_STACK[-1]
        self.BLOCK_STACK.append(out)
        out.children = [child.copy() for child in self.children if child is not None]
        self.BLOCK_STACK.pop()
        return out

    def reset(self):
        super().reset()
        self.variables: dict[str, "VariableObj"] = {}
        self.BLOCK_STACK.append(self)
        for x in self.children:
            x.reset()
        self.BLOCK_STACK.pop()
        # {name: VarObj, ...} -- recursive import uppon proper type annotation
        self.builder = None
        self.last_instruction = False
        self.ended = False

    def append_nested_vars(self):
        '''append vars for nested blocks'''
        if len(self.BLOCK_STACK) != 0:
            self.variables = {**self.variables,
                              **self.BLOCK_STACK[-1].variables}

    def fullfill_templates(self, func):
        for child in self:
            child.fullfill_templates(func)

    def post_parse(self, func):
        for child in self:
            child.post_parse(func)

    def pre_eval(self, func):
        for x in self:
            x.pre_eval(func)

    def eval_impl(self, func):
        from Ast.functions.definition import FunctionDef
        from Ast.module import Module

        if len(self.children) == 0:
            self.last_instruction = not func.ret_type.is_void()
            return
        self.BLOCK_STACK.append(self)
        for x in self.children[0:-1]:
            if not isinstance(func, Module):
                if (func.has_return or self.ended) and not isinstance(x, FunctionDef):
                    continue
            x.eval(func)
        if not isinstance(func, Module):
            self.last_instruction = not func.ret_type.is_void()
            if not (func.has_return or self.ended) or isinstance(x, FunctionDef):
                self.children[-1].eval(func)
        else:
            self.children[-1].eval(func)

        self.BLOCK_STACK.pop()

    def __iter__(self) -> Iterator[Any]:
        if len(self.children) == 0:
            return
        self.BLOCK_STACK.append(self)  # type: ignore
        for child in self.children[0:-1]:
            yield child
            if self.ended:
                self.BLOCK_STACK.pop()
                return
        yield self.children[-1]
        self.BLOCK_STACK.pop()

    def get_variable(self, var_name: str, module=None):
        '''get variable by name'''
        if var_name in self.variables.keys():
            return self.variables[var_name]
        elif self.parent is not None:
            return self.parent.get_variable(var_name, module)
        elif module is not None:
            value = module.get_global(var_name)
            if value is None:
                return None
            return value.obj

    def get_type_by_name(self, var_name, pos):
        if self.parent is not None:
            return self.parent.get_type_by_name(var_name, pos)
        if self.module is not None:
            return self.module.get_type_by_name(var_name, pos)

    def create_const_var(self, func, typ):
        ptr = func.create_const_var(typ)
        self.constants.append((ptr, typ))
        return ptr

    def register_dispose(self, func, node):
        self.dispose_queue.append(node)
        func.register_dispose(node)

    def validate_variable(self, var_name: str, module=None) -> bool:
        '''Return true if a variable already has a ptr'''
        var_ptr = self.get_variable(var_name, module).ptr  # type: ignore
        return var_ptr is not None

    def validate_variable_exists(self, var_name: str, module=None) -> bool:
        if self.parent is None and module is not None:
            return (var_name in self.variables.keys()) or \
                (module.get_global(var_name) is not None)
        return (var_name in self.variables.keys()) or \
            self.parent.validate_variable_exists(var_name, module)

    def repr_as_tree(self) -> str:
        return self.create_tree("Block",
                                contents=self.children,
                                variables=self.variables)


# Utility functions :)
def get_current_block() -> Block:
    return Block.BLOCK_STACK[-1]


def create_const_var(func, typ) -> ir.AllocaInstr:
    block = get_current_block()
    return block.create_const_var(func, typ)
