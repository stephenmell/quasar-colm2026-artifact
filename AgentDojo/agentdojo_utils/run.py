#
#
import inspect
from dataclasses import dataclass

#
from epic import (
    graph_semantics,
)

@dataclass
class Context:
    LOCK : int
    CALLS: int
    ROUNDS : any

def make_stepped(translator, function, CONTEXT):
    if inspect.iscoroutinefunction(function) and (not inspect.isgeneratorfunction(function) or inspect.isasyncgenfunction(function)):
        async def wrapper(*args, **kwargs):
            CONTEXT.CALLS += 1
            lock = CONTEXT.LOCK
            await graph_semantics.REDUCTION_STUCK_EVENT.wait()
            if CONTEXT.LOCK == lock:
                CONTEXT.LOCK += 1
                CONTEXT.ROUNDS.append(CONTEXT.CALLS)
                CONTEXT.CALLS = 0
            return await function(*args, **kwargs)
    else:
        async def wrapper(*args, **kwargs):
            CONTEXT.CALLS += 1
            lock = CONTEXT.LOCK
            await graph_semantics.REDUCTION_STUCK_EVENT.wait()
            if CONTEXT.LOCK == lock:
                CONTEXT.LOCK += 1
                CONTEXT.ROUNDS.append(CONTEXT.CALLS)
                CONTEXT.CALLS = 0
            return function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return translator.WrappedCallable(function, wrapper)