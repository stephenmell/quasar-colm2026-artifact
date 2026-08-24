import os

from .env import *
from .color_printing import *
from .formatting import *

def get_terminal_size() -> Tuple[int, int]:
    # Could use `os.get_terminal_size()`, except it behaves poorly with `less` (checkes stdout, not tty)
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(rows), int(columns)

def print_trace(
        expr : Function,
        reducer : Callable[[Function], Iterable[Function]],
        u : Optional[VarUniquifier] = None,
    ):
    if u is None: u = var_name_uniquifier()
    il_as_lines(ppil_function(expr, None, u))
    print("========")
    # all_terms = frozenset({expr}) | frozenset(e for _steps, e in hist) | term_from_step(steps for steps, _e in hist)
    for e in reducer(expr):
        print("--------")
        # print("Steps:", "; ".join(sorted(fmt_step(step, u) for step in steps)))
        il_as_lines(ppil_function(e, None, u))
        print("========")

def print_twocolumn_trace(
        expr : Function,
        reducer : Callable[[Function], Iterable[Function]],
        width : Optional[int] = None,
        u : Optional[VarUniquifier] = None,
        pause : bool = False,
    ):
    if width is None:
        width = get_terminal_size()[1]
    if u is None: u = var_name_uniquifier()
    prev = expr
    for e in reducer(expr):
        print("".join(("=",) * width))
        before_il, after_il = stepping_pair_to_indented_lines(prev, e)
        before_lines = il_as_lines(before_il)
        after_lines = il_as_lines(after_il)
        cl_print(word_wrap_multi_cl_twocolumn(before_lines, after_lines, width, cs_cat(" || ")))
        prev = e
        if pause:
            input("STEP >>")

def print_func(f : Function):
    return cl_print(il_as_lines(ppil_function(f)))

def print_final(expr : Function, semant : Callable[[Function], Iterable[Function]]):
    trace = tuple(semant(expr))
    print_func(trace[-1] if trace else expr)