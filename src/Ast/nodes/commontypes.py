'''A poorly named file that contains important types
such as `SrcPosition` named tuple
'''

from typing import NamedTuple, Union


class SrcPosition(NamedTuple):
    line: int
    col: int
    length: int
    source_name: str


GenericNode = Union["ASTNode", "ExpressionNode"]