from typing import Any, Iterator, Self

from Ast.nodes import ASTNode
from Ast.nodes.commontypes import GenericNode, SrcPosition


class ContainerNode(ASTNode):
    '''A node consistening of other nodes.
    Containers do not directly do operations on these nodes
    '''
    __slots__ = ("children", )

    def __init__(self, position: SrcPosition, *args, **kwargs):
        self.children: list = []
        super().__init__(position, *args, **kwargs)

    def __iter__(self) -> Iterator[Any]:
        yield from self.children

    def append_child(self, child: GenericNode):
        '''append child to container.'''
        self.children.append(child)

    def append_children(self, child: GenericNode | Self):
        '''possible to append 1 or more children'''
        if isinstance(child, ContainerNode):
            self.children += child.children
            return
        self.append_child(child)