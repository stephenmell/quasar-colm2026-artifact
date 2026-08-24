from typing import TypeAlias
from typing import (
    Union as Union,
    Tuple as Tuple,
    Literal as Literal,
    TypeAlias as TypeAlias,
    Callable as Callable,
    TypeVar as TypeVar,
    Optional as Optional,
    FrozenSet as FrozenSet,
    MutableSet as MutableSet,
    Iterable as Iterable,
    Iterator as Iterator,
    AsyncIterable as AsyncIterable,
    AsyncIterator as AsyncIterator,
    List as List,
    Dict as Dict,
    NewType as NewType,
    Generic as Generic,
    Protocol as Protocol,
    Sequence as Sequence,
    overload as overload,
    Awaitable as Awaitable,
    Coroutine as Coroutine,
    ParamSpec as ParamSpec,
)
import typing
Object = object
_T = TypeVar("_T")
Continuation: TypeAlias = Callable[[_T], None]
Thunk: TypeAlias = Callable[[], _T]
IList: TypeAlias = Tuple[_T, ...]
Cell: TypeAlias = List[_T]

from dataclasses import dataclass as dataclass
from async_lru import alru_cache as alru_cache # type: ignore
import asyncio

def cast(x : typing.Any) -> typing.Any:
    return x

def async_iter_to_sync(ai : AsyncIterable[_T]) -> Iterable[_T]:
    eos = object()
    ao = aiter(ai)
    while True:
        ax = anext(ao, eos)
        x = asyncio.get_event_loop().run_until_complete(ax)
        if x is eos:
            break
        else:
            yield x # type: ignore

def UNIMPLEMENTED(*args : typing.Any, **kwargs : typing.Any) -> typing.Any:
    raise NotImplemented


class Linear(Generic[_T]):
    value : Optional[_T]

    def __init__(self, value : _T):
        self.value = value
    
    def use(self) -> _T:
        assert self.value is not None
        ret = self.value
        self.value = None
        return ret

def async_iter_caching(ai : AsyncIterable[_T]) -> Thunk[AsyncIterator[_T]]:
    # print("Make cache for", id(ai))
    items : List[_T] = []
    is_done : Cell[bool] = [False]
    event_more = asyncio.Event()

    async def consumer():
        async for c in ai:
            items.append(c)
            event_more.set()
        is_done[0] = True
        event_more.set()
    asyncio.create_task(consumer())

    async def ret() -> AsyncIterator[_T]:
        # o = object()
        # print("Instantiated", id(ai), "as", id(o))
        i = 0
        while True:
            if i < len(items):
                # print("Yielded", id(ai), "as", id(o), i)
                yield items[i]
                i += 1
            else:
                if is_done[0]:
                    break
                else:
                    event_more.clear()
                    await event_more.wait()
    return ret

def int_dict_as_contiguous(d : Dict[int, _T]) -> IList[_T]:
    out : List[Optional[_T]] = [None] * len(d)
    for i, v in d.items():
        out[i] = v
    # safe by the pigeonhole principle
    return tuple(out) # type: ignore