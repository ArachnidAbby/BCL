from enum import Enum


class NodeTypes(Enum):
    DEFAULT       = 1
    EXPRESSION    = 2
    STATEMENT     = 3
    BLOCK         = 4
    KV_PAIR       = 5
