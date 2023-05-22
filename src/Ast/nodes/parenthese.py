from typing import Any, Iterator

from llvmlite import ir

import Ast.Ast_Types as Ast_Types
from Ast.nodes import ContainerNode
from Ast.nodes.commontypes import GenericNode, SrcPosition
from Ast.nodes.keyvaluepair import KeyValuePair
from errors import error


class ParenthBlock(ContainerNode):
    '''Provides a node for parenthesis as an expression or tuple'''
    __slots__ = ('ret_type', 'in_func_call', 'ptr',
                 'contains_ellipsis', 'evaled_children')

    def __init__(self, pos: SrcPosition, *args, **kwargs):
        super().__init__(pos, *args, **kwargs)
        self.in_func_call = False
        self.ptr = None
        self.ret_type = Ast_Types.Void()
        self.evaled_children = []
        self.contains_ellipsis = False

    def pre_eval(self, func):
        for child in self.children:
            child.pre_eval(func)

        if len(self.children) == 1:
            self.ret_type = self.children[0].ret_type
        else:
            members = [child.ret_type for child in self.children]
            self.ret_type = Ast_Types.TupleType(members)

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
                self.evaled_children.append(ptr)
                continue
            self.evaled_children.append(child.eval(func))

    def eval(self, func):
        self.evaled_children = []
        self._pass_as_pointer_changes(func)
        if len(self.children) == 1:
            return self.evaled_children[0]
        elif not self.in_func_call:
            if self.ptr is None:
                self.ptr = func.create_const_var(self.ret_type)
                for c, child in enumerate(self.evaled_children):
                    child_ptr = \
                        func.builder.gep(self.ptr,
                                         [ir.Constant(ir.IntType(32), 0),
                                          ir.Constant(ir.IntType(32), c)])
                    func.builder.store(child, child_ptr)

            return func.builder.load(self.ptr)

    def __repr__(self) -> str:
        children_repr = (repr(x) for x in self.children)
        return f'<Parenth Block: \'({", ".join(children_repr)})\'>'

    def __str__(self) -> str:
        children_repr = (str(x) for x in self.children)
        return f'({", ".join(children_repr)})'

    def get_ptr(self, func):
        '''allocate to stack and get a ptr'''
        # if len(self.children) > 1:
        #     error("Cannot get a ptr to a set of parentheses with more than " +
        #           "one value", line=self.position)

        if self.ptr is None:
            val = self.eval(func)

            if len(self.children) == 1:
                self.ptr = func.create_const_var(self.ret_type)
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

    def as_type_reference(self, func):
        if len(self.children) == 1:
            return self.children[0].as_type_reference(func)
        else:
            members = [child.as_type_reference(func) for child in self.children]
            return Ast_Types.TupleType(members)
