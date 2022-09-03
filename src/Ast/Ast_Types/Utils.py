from enum import Enum, EnumMeta, IntEnum, auto


from . import Type_Base
from Errors import error

# Todo: improve cases-sensitivity.
class CaseInsensitiveEnumMeta(EnumMeta):
    '''Allow fetching of type-names without case-sensitivity. 
    The case-sensitivity will later be readded, but for the time being, this remains.
    '''
    def __getitem__(self, item):
        if not isinstance(item, str):
            raise ValueError(item)
        elif item.upper() not in self._member_names_:
            return item

        return super().__getitem__(item.upper())  # type: ignore

class Types(IntEnum, metaclass=CaseInsensitiveEnumMeta):
    '''Known return-types in the language.'''
    UNKNOWN = auto()
    KV_PAIR = auto()
    VOID    = auto()
    BOOL    = auto()
    I32     = auto()
    I64     = auto()
    INT     = auto()
    F64     = auto()
    F128    = auto()
    FLOAT   = auto()

    @property
    def value(self):
        return Type_Base.types_dict[self._name_.lower()]
