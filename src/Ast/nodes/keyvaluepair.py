from typing import Any

from Ast.nodes import ASTNode
from Ast.nodes.commontypes import SrcPosition


class KeyValuePair(ASTNode):
    '''Key-Value pairs for use in things like structs, functions, etc.'''
    __slots__ = ('key', 'value')
    # type = NodeTypes.KV_PAIR
    # name = "kv_pair"

    def __init__(self, pos: SrcPosition, k, v):
        super().__init__(pos)
        self.key = k
        self.value = v

    def validate_type(self):  # TODO: REMOVE, DUPLICATE
        return self.value.as_type_reference()

    def get_type(self) -> Any:
        '''Get and validate type'''
        return self.value.as_type_reference()

    @property
    def position(self) -> SrcPosition:
        return self.merge_pos((self.value.position, ))