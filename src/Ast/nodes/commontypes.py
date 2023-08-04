'''A poorly named file that contains important types
such as `SrcPosition` named tuple
'''

from enum import Enum
from typing import Any, NamedTuple, Union


class SrcPosition(NamedTuple):
    line: int
    col: int
    length: int
    source_name: str = ""

    @staticmethod
    def invalid():
        return SrcPosition(-1, -1, -1, '')

    @property
    def is_invalid(self):
        return self == self.invalid()


class MemberInfo(NamedTuple):
    mutable: bool
    is_pointer: bool
    typ: Any  # can't fully qualify this because circular imports


class Modifiers:
    VISIBILITY_PUBLIC = 0
    VISIBILITY_PRIVATE = 1


class Lifetimes(Enum):
    UNKNOWN = 0
    LOCAL = 1
    FUNCTION = 2
    LONG = 3


GenericNode = Union["ASTNode", "ExpressionNode"]  # NOQA: F821 # type: ignore
# no way around the previous hack as far as I know
