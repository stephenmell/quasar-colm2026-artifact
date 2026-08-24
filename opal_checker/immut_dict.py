import os
import sys
import builtins
from typing import (
    overload,
    TypeVar,
)

#
from opal_checker.immut_common import IllegalMutationException

_T = TypeVar("_T")
_S = TypeVar("_S")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")


class dict[_KT, _VT](builtins.dict[_KT, _VT]):
    @overload
    def pop(self, key: _KT, /) -> _VT: ...
    @overload
    def pop(self, key: _KT, default: _VT, /) -> _VT: ...
    def pop(self, key: _KT, default: _T, /) -> _VT | _T: # pyright: ignore[reportIncompatibleMethodOverride, reportInconsistentOverload]
        raise IllegalMutationException("dict.pop")

    def __setitem__(self, key: _KT, value: _VT, /) -> None:
        raise IllegalMutationException("dict.__setitem__")

    def __delitem__(self, key: _KT, /) -> None:
        raise IllegalMutationException("dict.__delitem__")
