import os
import sys
import builtins
from typing import (
    SupportsIndex, 
    Iterable, 
    Callable, 
    overload, 
    TYPE_CHECKING
)
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparisonT, SupportsRichComparison

#
from opal_checker.immut_common import IllegalMutationException

class list[_T](builtins.list[_T]):
    def append(self, object: _T, /) -> None:
        raise IllegalMutationException("list.append")
    def extend(self, iterable: Iterable[_T], /) -> None:
        raise IllegalMutationException("list.extend")
    def pop(self, index: SupportsIndex = -1, /) -> _T:
        raise IllegalMutationException("list.pop")
    def insert(self, index: SupportsIndex, object: _T, /) -> None:
        raise IllegalMutationException("list.insert")
    def remove(self, value: _T, /) -> None:
        raise IllegalMutationException("list.remove")
    @overload
    def sort(self: list["SupportsRichComparisonT"], *, key: None = None, reverse: bool = False) -> None: ... # pyright: ignore[reportInconsistentOverload]
    def sort(self, *, key: Callable[[_T], "SupportsRichComparison"], reverse: bool = False) -> None: # pyright: ignore[reportInconsistentOverload, reportIncompatibleMethodOverride]
        raise IllegalMutationException("list.sort")
    @overload
    def __setitem__(self, key: SupportsIndex, value: _T, /) -> None: ... # pyright: ignore[reportInconsistentOverload]
    def __setitem__(self, key: slice, value: Iterable[_T], /) -> None: # pyright: ignore[reportInconsistentOverload, reportIncompatibleMethodOverride]
        raise IllegalMutationException("list.__setitem__")
    def __delitem__(self, key: SupportsIndex | slice, /) -> None:
        raise IllegalMutationException("list.__delitem__")
