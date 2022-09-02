from enum import Enum, EnumMeta

from Errors import error

class CaseInsensitiveEnumMeta(EnumMeta):
    def __getitem__(self, item):
        if not isinstance(item, str):
            raise ValueError(item)
        elif item.upper() not in self._member_names_:
            return item

        return super().__getitem__(item.upper())  # type: ignore

class Types(Enum, metaclass=CaseInsensitiveEnumMeta):
    UNKNOWN = 0
    KV_PAIR = 1
    VOID    = 2
    BOOL    = 3
    I32     = 4
    I64     = 5
    INT     = 6
    F64     = 7
    F128    = 8
    FLOAT   = 9