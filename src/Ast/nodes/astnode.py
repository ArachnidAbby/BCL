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
    isconstant: bool = False

    def __init__(self, position: SrcPosition, *args, **kwargs):
        self._position = position        # (line#, col#, len)

    def is_expression(self):
        '''check whether or not a node is an expression'''
        return False

    def post_parse(self, parent):
        '''Happens before pre_eval but after parsing
        This creates globals. Ex: functions
        '''

    def pre_eval(self, func):
        '''pre eval step that is usually used to validate
        the contents of a node
        '''

    def eval(self, func):
        '''eval step, often returns ir.Instruction'''

    def merge_pos(self, positions: Tuple[SrcPosition, ...]) -> SrcPosition:
        current_pos = self._position
        new_pos = list(self._position)
        for x in positions:
            # len of current position ptr VV
            current_len = (current_pos.length + current_pos.col-1)
            end_pos = (x.col-current_len)+x.length
            new_pos[2] = end_pos

        return SrcPosition(*new_pos)  # type: ignore

    def get_position(self) -> SrcPosition:
        return self._position

    @property
    def position(self) -> SrcPosition:
        return self.get_position()

    @position.setter
    def position(self, val):
        self._position = val

    def repr_as_tree(self) -> str:
        return repr(self)

    def create_tree_list(self, parent_repr, children) -> str:
        output = f'/ {parent_repr}:\n'
        for child in children:
            if isinstance(child, ASTNode):
                child_str = child.repr_as_tree().replace('\n', '\n|\t')
                output += f"\n|\t{child_str}"
            else:
                output += f"\n|\t{repr(child)}"
        return output

    def create_tree_dict(self, parent_repr: str, children) -> str:
        output = f'/ {parent_repr}:\n'
        for child_name in children.keys():
            child = children[child_name]
            if isinstance(child, ASTNode):
                child_str = child.repr_as_tree().replace('\n', '\n|\t')
                output += f"|\t{child_name}: {child_str}\n"
            elif isinstance(child, dict):
                sub_tree = self.create_tree_dict('dict', child)
                sub_tree_str = sub_tree.replace('\n', '\n|\t') + '\n'
                output += f"|\t{child_name}: {sub_tree_str}"
            elif isinstance(child, list):
                sub_tree = self.create_tree_list('list', child)
                sub_tree_str = sub_tree.replace('\n', '\n|\t') + '\n'
                output += f"|\t{child_name}: {sub_tree_str}"
            else:
                output += f"|\t{child_name}: {repr(child)}\n"
        return output

    def create_tree(self, parent_repr: str, **children) -> str:
        return self.create_tree_dict(parent_repr, children)
