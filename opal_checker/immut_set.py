import os
import sys
import builtins
from typing import (
    Iterable, 
    Any
)

#
from opal_checker.immut_common import IllegalMutationException

class set[_T](builtins.set[_T]):
    def add(self, element: _T, /) -> None:
        raise IllegalMutationException("set.add")
    def difference_update(self, *s: Iterable[Any]) -> None:
        raise IllegalMutationException("set.difference_update")
    def discard(self, element: _T, /) -> None:
        raise IllegalMutationException("set.discard")
    def intersection_update(self, *s: Iterable[Any]) -> None:
        raise IllegalMutationException("set.intersection_update")
    def remove(self, element: _T, /) -> None:
        raise IllegalMutationException("set.remove")
    def symmetric_difference_update(self, s: Iterable[_T], /) -> None:
        raise IllegalMutationException("set.symmetric_difference_update")
    def update(self, *s: Iterable[_T]) -> None:
        raise IllegalMutationException("set.update")