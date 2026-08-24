from __future__ import annotations
from dataclasses import dataclass
from typing import TypeVar, Generic, Union, Tuple, FrozenSet, Literal
import itertools
import operator

T = TypeVar("T")

# Replace this with actual IList definition or use Tuple
IList = Tuple

@dataclass(frozen=True)
class AbstractTuple(Generic[T]):
    _items: IList[Tuple[T, bool]]

    def __len__(self):
        lb = 0
        ub = 0
        for _item, certain in self._items:
            ub += 1
            if certain:
                lb += 1
        return AbstractOther(frozenset(range(lb, ub + 1)))

    def __getitem__(self, index):
        assert index == 0

        ret = []
        for x, certain in self._items:
            ret.append(x)
            if certain:
                break

        return AbstractOther(frozenset(ret))


def do_pairwise(f, self, other):
    if type(self) is not AbstractOther and type(other) is not AbstractOther:
        return f(self, other)

    if type(self) is not AbstractOther:
        self = AbstractOther(frozenset((self,)))
    if type(other) is not AbstractOther:
        other = AbstractOther(frozenset((other,)))
    return join_many(f(a, b) for a, b in itertools.product(self._possibilities, other._possibilities))


def do_unary(f, self):
    if type(self) is not AbstractOther:
        return f(self)
    else:
        return join_many(f(x) for x in self._possibilities)


@dataclass
class AbstractTupleUnion:
    pass


@dataclass(frozen=True)
class AbstractOther(Generic[T]):
    _possibilities: FrozenSet[T]

    def __post_init__(self):
        for x in self._possibilities:
            assert type(x) not in ABSTRACT_TYPES

    def __add__(self, other): return do_pairwise(operator.add, self, other)
    def __radd__(self, other): return do_pairwise(operator.add, other, self)
    def __sub__(self, other): return do_pairwise(operator.sub, self, other)
    def __rsub__(self, other): return do_pairwise(operator.sub, other, self)
    def __mul__(self, other): return do_pairwise(operator.mul, self, other)
    def __rmul__(self, other): return do_pairwise(operator.mul, other, self)
    def __floordiv__(self, other): return do_pairwise(operator.floordiv, self, other)
    def __rfloordiv__(self, other): return do_pairwise(operator.floordiv, other, self)
    def __truediv__(self, other): return do_pairwise(operator.truediv, self, other)
    def __rtruediv__(self, other): return do_pairwise(operator.truediv, other, self)
    def __abs__(self): return do_unary(abs, self)
    
    def __or__(self, other): return do_pairwise(operator.or_, self, other)
    def __ror__(self, other): return do_pairwise(operator.or_, other, self)
    def __and__(self, other): return do_pairwise(operator.and_, self, other)
    def __rand__(self, other): return do_pairwise(operator.and_, other, self)

    def __lt__(self, other): return do_pairwise(operator.lt, self, other)
    def __le__(self, other): return do_pairwise(operator.le, self, other)
    def __eq__(self, other): return do_pairwise(operator.eq, self, other)
    def __ne__(self, other): return do_pairwise(operator.ne, self, other)
    def __ge__(self, other): return do_pairwise(operator.ge, self, other)
    def __gt__(self, other): return do_pairwise(operator.gt, self, other)

    def __getattr__(self, item):
        return do_unary(lambda x: getattr(x, item), self)

    def __call__(self, *args, **kwargs):
        for arg in args:
            assert type(arg) not in ABSTRACT_TYPES, (args, kwargs)
        for arg in kwargs.values():
            assert type(arg) not in ABSTRACT_TYPES, (args, kwargs)
        return do_unary(lambda x: x(*args, **kwargs), self)


ABSTRACT_TYPES = frozenset({AbstractOther, AbstractTuple, AbstractTupleUnion})

ABS_BOOL_TOP = AbstractOther(frozenset({False, True}))
ABS_BOOL_FALSE = AbstractOther(frozenset({False}))
ABS_BOOL_TRUE = AbstractOther(frozenset({True}))

def get_abstract_bool_value(b: AbstractOther[bool]) -> Union[Literal[False], Literal[True], Literal["TOP"]]:
    assert type(b) is AbstractOther
    val: Union[Literal[False], Literal[True], Literal["TOP"], None] = None
    for x in b._possibilities:
        assert type(x) is bool, b
        if val is None:
            val = x
        if x != val:
            val = "TOP"
    assert val is not None
    return val

def join(a, b):
    if a is b:
        return a

    if type(a) is AbstractTuple or type(b) is AbstractTuple or \
       type(a) is AbstractTupleUnion or type(b) is AbstractTupleUnion:
        return AbstractTupleUnion()

    if type(a) is AbstractOther:
        a_poss = a._possibilities
    else:
        a_poss = frozenset({a})

    if type(b) is AbstractOther:
        b_poss = b._possibilities
    else:
        b_poss = frozenset({b})

    return AbstractOther(a_poss.union(b_poss))

def join_many(xs):
    ret = AbstractOther(frozenset())
    for x in xs:
        ret = join(ret, x)
    return ret

def join_vars(a_l: IList[T], b_l: IList[T]) -> IList[T]:
    assert len(a_l) == len(b_l)
    ret: IList[T] = ()
    for a, b in zip(a_l, b_l):
        ret += (join(a, b),)
    return ret

def concrete_for_loop(for_body, l, lvars):
    for x in l:
        lvars = for_body(x, *lvars)
    return lvars

def concrete_if_stmt(then_body, else_body, b, lvars):
    if b:
        lvars = then_body(*lvars)
    else:
        if else_body is not None:
            lvars = else_body(*lvars)
    return lvars

def abstract_for_loop(for_body, l, lvars):
    if not isinstance(l, AbstractTuple):
        return concrete_for_loop(for_body, l, lvars)

    for x, certain in l._items:
        lvars_new = for_body(x, *lvars)
        if certain:
            lvars = lvars_new
        else:
            lvars = join_vars(lvars, lvars_new)
    return lvars

def abstract_if_stmt(then_body, else_body, b: Union[bool, AbstractOther[bool]], lvars):
    if isinstance(b, bool):
        b = AbstractOther(frozenset({b}))
    val = get_abstract_bool_value(b)

    if val is True:
        lvars = then_body(*lvars)
    elif val is False:
        if else_body is not None:
            lvars = else_body(*lvars)
    elif val == "TOP":
        lvars_t = then_body(*lvars)
        lvars_f = else_body(*lvars) if else_body is not None else lvars
        lvars = join_vars(lvars_t, lvars_f)
    else:
        assert False, b
    return lvars

def ensure_abs_type(x, t):
    if isinstance(x, AbstractOther):
        for y in x._possibilities:
            assert isinstance(y, t), (y, t)
    else:
        assert isinstance(x, t), (x, t)

def abstract_not_expr(x):
    return do_unary(lambda y: not y, x)

def abstract_and_expr(a, b):
    return do_pairwise(lambda y, z: y and z, a, b)

def abstract_or_expr(a, b):
    return do_pairwise(lambda y, z: y or z, a, b)

def abstract_bool_to_yesno(x: bool):
    ensure_abs_type(x, bool)
    return do_unary(lambda y: "yes" if y else "no", x)

def abstract_len(x):
    return x.__len__()
