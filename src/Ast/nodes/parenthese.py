from typing import Any, Iterator

import Ast.Ast_Types as Ast_Types
from Ast.nodes import ContainerNode
from Ast.nodes.commontypes import GenericNode, SrcPosition
from Ast.nodes.keyvaluepair import KeyValuePair
from errors import error


class ParenthBlock(ContainerNode):
    '''Provides a node for parenthesis as an expression or tuple'''
    __slots__ = ('ret_type', 'in_func_call', 'ptr',
                 'contains_ellipsis')

    def __init__(self, pos: SrcPosition, *args, **kwargs):
        super().__init__(pos, *args, **kwargs)
        self.in_func_call = False
        self.ptr = None
        self.ret_type = Ast_Types.Void()
        self.contains_ellipsis = False

    def pre_eval(self, func):
        for child in self.children:
            child.pre_eval(func)

        # * tuples return `void` but an expr returns the same data as its child
        if len(self.children) == 1:
            self.ret_type = self.children[0].ret_type
        else:
            self.ret_type = Ast_Types.Void()

    # TODO: Should probably not use Iter[Any]
    def __iter__(self) -> Iterator[Any]:
        yield from self.children

    def is_key_value_pairs(self) -> bool:
        '''check if all children are `KV_pair`s,
        this is useful for func definitions'''
        for x in self.children:
            if not isinstance(x, KeyValuePair):
                return False
        return True

    def append_child(self, child: GenericNode):
        if child == "...":
            return
        self.children.append(child)

    def _pass_as_pointer_changes(self, func):
        '''changes child elements to be passed as pointers if needed'''
        for c, child in enumerate(self.children):
            # TODO: THIS IS SHIT
            if self.in_func_call and (child.ret_type.pass_as_ptr):
                ptr = child.get_ptr(func)
                self.children[c] = ptr
                continue
            self.children[c] = child.eval(func)

    def eval(self, func):
        # TODO: THIS SHOULD NOT MODIFY THE ORIGINAL
        self._pass_as_pointer_changes(func)
        if len(self.children) == 1:
            return self.children[0]

    def __repr__(self) -> str:
        children_repr = (repr(x) for x in self.children)
        return f'<Parenth Block: \'({", ".join(children_repr)})\'>'

    def get_ptr(self, func):
        '''allocate to stack and get a ptr'''
        if len(self.children) > 1:
            error("Cannot get a ptr to a set of parentheses with more than " +
                  "one value", line=self.position)

        if self.ptr is None:
            self.ptr = func.create_const_var(self.ret_type)
            val = self.eval(func)

            func.builder.store(val, self.ptr)
        return self.ptr

    @property
    def is_empty(self) -> bool:
        return len(self.children) == 0

    @property
    def ir_type(self):
        return self.ret_type.ir_type

    def repr_as_tree(self) -> str:
        return self.create_tree("Parenthesis",
                                children=self.children,
                                return_type=self.ret_type)