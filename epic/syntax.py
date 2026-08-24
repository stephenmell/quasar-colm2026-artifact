import asyncio
import typeguard

from .env import *

@dataclass(frozen=True)
class Var:
    id : int
    name : str

_symbol_next_id = 0
def var(name : str) -> Var:
    global _symbol_next_id
    ret = Var(_symbol_next_id, name)
    _symbol_next_id += 1
    return ret

Statement : TypeAlias = Union[
    Tuple[Literal["def"], Var, "Function"],                                 # def f func
    Tuple[Literal["call"], str, Tuple[Var, ...], Var, Tuple[Var, ...]],     # call call_name (y1, ..., ym) f (x1, ... xn)
    Tuple[Literal["pack"], Var, Tuple[Var, ...]],                           # pack p (x1, ... xn)
    Tuple[Literal["unpack"], Tuple[Var, ...], Var],                         # unpack (y1, ..., ym) p
    Tuple[Literal["prim"], Var, Object],                                    # prim y pyobj
    Tuple[Literal["task"], str, Tuple[Var, ...], "Task"],                   # task call_name (y1, ..., ym) pyfuture
    Tuple[Literal["loop"], Var, Var, Var],                                  # loop y initial body
]

Body : TypeAlias = Tuple[Tuple[Statement, ...], Tuple[Var, ...]]
Function : TypeAlias = Tuple[Tuple[Var, ...], "Body"]
Task : TypeAlias = asyncio.Task[Body]

def name_prefixed(name_prefix : str, name : str) -> str:
    return name
    # return name_prefix + "|" + name

def copy_var_binder(v : Var, substitution : Dict[Var, Var], name_prefix : str) -> Var:
    new_v = var(name_prefixed(name_prefix, v.name))
    substitution[v] = new_v
    return new_v

def copy_var_occurrence(v : Var, substitution : Optional[Dict[Var, Var]]) -> Var:
    if substitution is None: substitution = {}
    
    return substitution[v] if v in substitution else v

def copy_function(func : Function, substitution : Optional[Dict[Var, Var]], name_prefix : str) -> Function:
    if substitution is None: substitution = {}
    
    return (
        tuple(copy_var_binder(v, substitution, name_prefix) for v in func[0]),
        copy_body(func[1], substitution, name_prefix),
    )

def copy_body(body : Body, substitution : Optional[Dict[Var, Var]], name_prefix : str) -> Body:
    if substitution is None: substitution = {}

    return (
        tuple(copy_statement(stmt, substitution, name_prefix) for stmt in body[0]),
        tuple(copy_var_occurrence(v, substitution) for v in body[1]),
    )

def copy_statement(statement : Statement, substitution : Optional[Dict[Var, Var]], name_prefix : str) -> Statement:
    if substitution is None: substitution = {}

    match statement:
        case "def", f, func:
            ret = ("def",
                copy_var_binder(f, substitution, name_prefix),
                copy_function(func, substitution, name_prefix),
            )
        case "call", name, outps, f, inps:
            ret = ("call",
                name_prefixed(name_prefix, name),
                tuple(copy_var_binder(v, substitution, name_prefix) for v in outps),
                copy_var_occurrence(f, substitution),
                tuple(copy_var_occurrence(v, substitution) for v in inps),
            )
        case "pack", outp, inps:
            ret = ("pack",
                copy_var_binder(outp, substitution, name_prefix),
                tuple(copy_var_occurrence(v, substitution) for v in inps),
            )
        case "unpack", outps, inp:
            ret = ("unpack",
                tuple(copy_var_binder(v, substitution, name_prefix) for v in outps),
                copy_var_occurrence(inp, substitution),
            )
        case "prim", outp, pyobj:
            ret = ("prim",
                copy_var_binder(outp, substitution, name_prefix),
                pyobj,
            )
        case "task", name, outps, pyfuture:
            ret = ("task",
                name,
                tuple(copy_var_binder(v, substitution, name_prefix) for v in outps),
                pyfuture,
            )
        case "loop", outp, init, step:
            ret = ("loop",
                copy_var_binder(outp, substitution, name_prefix),
                copy_var_occurrence(init, substitution),
                copy_var_occurrence(step, substitution),
            )
        case x: assert False, x
    return ret

def substitute_var_occurrence(v : Var, substitution : Optional[Dict[Var, Var]]) -> Var:
    if substitution is None: substitution = {}
    
    return substitution[v] if v in substitution else v

def substitute_function(func : Function, substitution : Optional[Dict[Var, Var]]) -> Function:
    if substitution is None: substitution = {}
    
    return (
        func[0],
        substitute_body(func[1], substitution),
    )

def substitute_body(body : Body, substitution : Optional[Dict[Var, Var]]) -> Body:
    if substitution is None: substitution = {}

    return (
        tuple(substitute_statement(stmt, substitution) for stmt in body[0]),
        tuple(substitute_var_occurrence(v, substitution) for v in body[1]),
    )

def substitute_statement(statement : Statement, substitution : Optional[Dict[Var, Var]]) -> Statement:
    if substitution is None: substitution = {}

    match statement:
        case "def", f, func:
            ret = ("def",
                f,
                substitute_function(func, substitution),
            )
        case "call", name, outps, f, inps:
            ret = ("call",
                name,
                outps,
                substitute_var_occurrence(f, substitution),
                tuple(substitute_var_occurrence(v, substitution) for v in inps),
            )
        case "pack", outp, inps:
            ret = ("pack",
                outp,
                tuple(substitute_var_occurrence(v, substitution) for v in inps),
            )
        case "unpack", outps, inp:
            ret = ("unpack",
                outps,
                substitute_var_occurrence(inp, substitution),
            )
        case "prim", outp, pyobj:
            ret = ("prim",
                outp,
                pyobj,
            )
        case "task", name, outps, pyfuture:
            ret = ("task",
                name,
                outps,
                pyfuture,
            )
        case "loop", outp, init, step:
            ret = ("loop",
                outp,
                copy_var_occurrence(init, substitution),
                copy_var_occurrence(step, substitution),
            )
        case x: assert False, x
    return ret


def freevars_function(func : Function, out : MutableSet[Var], bound_vars : Optional[MutableSet[Var]] = None):
    if bound_vars is None: bound_vars = set()
    
    for v in func[0]:
        assert v not in out
        assert v not in bound_vars
        bound_vars.add(v)

    freevars_body(func[1], out, bound_vars)

def freevars_body(body : Body, out : MutableSet[Var], bound_vars : Optional[MutableSet[Var]] = None):
    if bound_vars is None: bound_vars = set()

    for stmt in body[0]:
        freevars_statement(stmt, out, bound_vars)
    
    for v in body[1]:
        if v not in bound_vars:
            out.add(v)

def freevars_statement(statement : Statement, out : MutableSet[Var], bound_vars : Optional[MutableSet[Var]] = None):
    if bound_vars is None: bound_vars = set()

    match statement:
        case "def", f, func:
            assert f not in out
            assert f not in bound_vars
            bound_vars.add(f)
            freevars_function(func, out, set(bound_vars))
        case "call", _name, outps, f, inps:
            if f not in bound_vars:
                out.add(f)
            for v in inps:
                if v not in bound_vars:
                    out.add(v)
            for v in outps:
                assert v not in out
                assert v not in bound_vars
                bound_vars.add(v)
        case "pack", outp, inps:
            for v in inps:
                if v not in bound_vars:
                    out.add(v)
            assert outp not in out
            assert outp not in bound_vars
            bound_vars.add(outp)
        case "unpack", outps, inp:
            if inp not in bound_vars:
                out.add(inp)
            for v in outps:
                assert v not in out
                assert v not in bound_vars
                bound_vars.add(v)
        case "prim", outp, _pyobj:
            assert outp not in out
            assert outp not in bound_vars
            bound_vars.add(outp)
        case "task", _name, outps, _pyfuture:
            for v in outps:
                assert v not in out
                assert v not in bound_vars
                bound_vars.add(v)
        case "loop", outp, init, step:
            if init not in bound_vars:
                out.add(init)
            if step not in bound_vars:
                out.add(step)
            assert outp not in out
            assert outp not in bound_vars
            bound_vars.add(outp)
        case x: assert False, x

def as_function(o : Object) -> Function:
    return typeguard.check_type(o, Function)
