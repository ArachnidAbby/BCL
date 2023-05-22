from typing import Any, Iterator, Self

from Ast.nodes import ASTNode
from Ast.nodes.commontypes import GenericNode, SrcPosition


class ContainerNode(ASTNode):
    '''A node consistening of other nodes.
    Containers do not directly do operations on these nodes
    '''
    __slots__ = ("children", "end_pos")

    def __init__(self, position: SrcPosition, *args, **kwargs):
        self.children: list = []
        self.end_pos = position
        super().__init__(position, *args, **kwargs)

    def __iter__(self) -> Iterator[Any]:
        yield from self.children

    def __len__(self) -> int:
        return len(self.children)

    def post_parse(self, parent):
        for child in self.children:
            child.post_parse(parent)

    def pre_eval(self, func):
        for child in self.children:
            child.pre_eval(func)

    def eval(self, func):
        for child in self.children:
            child.eval(func)

    def append_child(self, child: GenericNode):
        '''append child to container.'''
        self.children.append(child)

    def append_children(self, child: GenericNode | Self):
        '''possible to append 1 or more children'''
        if isinstance(child, ContainerNode):
            self.children += child.children
            return
        self.append_child(child)

    def set_end_pos(self, pos: SrcPosition):
        self.end_pos = pos

    def get_position(self) -> SrcPosition:
        return self.merge_pos((self._position, self.end_pos))
