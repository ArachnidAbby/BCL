from typing import Any, Iterator

import Ast.Ast_Types as Ast_Types
from Ast.nodes import ContainerNode
from Ast.nodes.commontypes import GenericNode, SrcPosition
from Ast.nodes.keyvaluepair import KeyValuePair
from errors import error


class ParenthBlock(ContainerNode):
    '''Provides a node for parenthesis as an expression or tuple'''
    __slots__ = ('ir_type', 'ret_type', 'in_func_call', 'ptr')
    # type = NodeTypes.EXPRESSION
    # name = "Parenth"

    def __init__(self, pos: SrcPosition, *args, **kwargs):
        super().__init__(pos, *args, **kwargs)
        self.ir_type = Ast_Types.Void().ir_type
        self.in_func_call = False
        self.ptr = None
        self.ret_type = Ast_Types.Void()

    def pre_eval(self, func):
        for c, child in enumerate(self.children):
            child.pre_eval(func)

        # * tuples return `void` but an expr returns the same data as its child
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Ast_Types.Void()
        self.ir_type = self.ret_type.ir_type

    def __iter__(self) -> Iterator[Any]:
        yield from self.children

    def is_key_value_pairs(self) -> bool:
        '''check if all children are `KV_pair`s, this is useful for func definitions'''
        for x in self.children:
            if not isinstance(x, KeyValuePair):
                return False
        return True

    def append_child(self, child: GenericNode):
        self.children.append(child)
        self.ret_type = self.children[0].ret_type if len(self.children)==1 else Ast_Types.Void()

    def _pass_as_pointer_changes(self, func):
        '''changes child elements to be passed as pointers if needed'''
        for c, child in enumerate(self.children):
            if self.in_func_call and (child.ret_type.pass_as_ptr or child.ret_type.name=='strlit'):
                ptr = child.get_ptr(func)
                self.children[c] = ptr
                continue
            self.children[c] = child.eval(func)

    def eval(self, func):
        self._pass_as_pointer_changes(func)  # TODO: THIS SHOULD NOT MODIFY THE ORIGINAL
        if len(self.children) == 1:
            return self.children[0]

    def __repr__(self) -> str:
        return f'<Parenth Block: \'({", ".join((repr(x) for x in self.children))})\'>'

    def get_ptr(self, func):
        '''allocate to stack and get a ptr'''
        if len(self.children) > 1:
            error("Cannot get a ptr to a set of parentheses with more than one value", line=self.position)

        if self.ptr is None:
            self.ptr = func.create_const_var(self.ret_type)
            val = self.eval(func)

            func.builder.store(val, self.ptr)
        return self.ptr
