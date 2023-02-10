'''A poorly named file that contains important types
such as `SrcPosition` named tuple
'''

from typing import NamedTuple, Union


class SrcPosition(NamedTuple):
    line: int
    col: int
    length: int
    source_name: str = ""

    @staticmethod
    def invalid():
        return SrcPosition(-1, -1, -1)


GenericNode = Union["ASTNode", "ExpressionNode"]  # NOQA: F821 # type: ignore
# no way around the previous hack as far as I know
