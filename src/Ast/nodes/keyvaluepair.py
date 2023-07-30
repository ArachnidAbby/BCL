from typing import Any

from Ast.nodes import ASTNode
from Ast.nodes.commontypes import SrcPosition, Modifiers
import errors

class KeyValuePair(ASTNode):
    '''Key-Value pairs for use in things like structs, functions, etc.'''
    __slots__ = ('key', 'value')
    # type = NodeTypes.KV_PAIR
    # name = "kv_pair"

    can_have_modifiers = True

    def __init__(self, pos: SrcPosition, k, v):
        super().__init__(pos)
        self.key = k
        self.value = v

    def copy(self):
        return KeyValuePair(self._position, self.key.copy(), self.value.copy())

    def fullfill_templates(self, func):
        self.key.fullfill_templates(func)
        self.value.fullfill_templates(func)

    def post_parse(self, func):
        self.key.post_parse(func)
        self.value.post_parse(func)

    def validate_type(self, func):  # TODO: REMOVE, DUPLICATE
        return self.value.as_type_reference(func)

    def ensure_unmodified(self):
        if self.visibility == Modifiers.VISIBILITY_PUBLIC:
            errors.error("Cannot have visibility modifier", line=self.position)

    def get_type(self, func) -> Any:
        '''Get and validate type'''
        return self.value.as_type_reference(func)

    def get_position(self) -> SrcPosition:
        return self.merge_pos((self.value.position, ))

    def repr_as_tree(self) -> str:
        return self.create_tree("Key Value Pair",
                                key=self.key,
                                value=self.value)
