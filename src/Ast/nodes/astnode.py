from typing import Tuple

from Ast.nodes.commontypes import SrcPosition


class ASTNode:
    '''Most basic Ast-Node that all others inherit from.
    This just provides standardization between Ast-Nodes.

    Methods required for classes inheriting this class:
    ====================================================
    * init -- method run uppon instantiation.
    This can take any # of args and kwargs
    * pre_eval -- run before eval(). Often used to validate certain conditions,
    such as a function or variable existing, return type, etc.
    * eval -- returns ir.Instruction object or None.
    This is used when construction final ir code.
    '''
    __slots__ = ('_position')

    is_operator: bool = False
    assignable: bool = False  # TODO: IMPLEMENT
    constant: bool = False  # TODO: USE THIS FOR ARRAY INDEXING. THIS SHOULD BE TRUE FOR LITERALS
    # type: NodeTypes = NodeTypes.DEFAULT # TODO: REMOVE
    # name: str = "AST_NODE"

    def __init__(self, position: SrcPosition, *args, **kwargs):
        self._position = position        # (line#, col#, len)

        # self.init(*args, **kwargs)

    def is_expression(self):
        '''check whether or not a node is an expression'''
        return False

    # def init(self, *args):
    #     '''initialize the node'''

    def pre_eval(self, func):
        '''pre eval step that is usually used to validate the contents of a node'''

    def eval(self, func):
        '''eval step, often returns ir.Instruction'''

    def merge_pos(self, positions: Tuple[SrcPosition, ...]) -> SrcPosition:
        new_pos = list(self._position)
        for x in positions:
            current_len = (new_pos[2]+new_pos[1]-1)  # len of current position ptr
            end_pos = (x[1]-current_len)+x[2]
            new_pos[2] = end_pos

        return tuple(new_pos)  # type: ignore

    @property
    def position(self) -> SrcPosition:
        return self._position

    @position.setter
    def position(self, val):
        self._position = val
