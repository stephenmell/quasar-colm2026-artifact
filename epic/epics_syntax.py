import os
import sys
import ast
import pprint
import typeguard

from .env import *
from . import syntax
from . import translator

Var = int

PyData = Union[str, int, None]
def check_pydata(p : Object) -> PyData:
    assert isinstance(p, str) or isinstance(p, int) or isinstance(p, float) or p is None, (type(p), repr(p), str(p))
    return p

Statement : TypeAlias = Union[
    Tuple[Literal["def"], Var, "Function"],                                 # def f func
    Tuple[Literal["call"], Tuple[Var, ...], Var, Tuple[Var, ...]],          # call (y1, ..., ym) f (x1, ... xn)
    Tuple[Literal["pack"], Var, Tuple[Var, ...]],                           # pack p (x1, ... xn)
    Tuple[Literal["unpack"], Tuple[Var, ...], Var],                         # unpack (y1, ..., ym) p
    Tuple[Literal["prim"], Var, PyData],                                    # prim y pyobj
]

Body : TypeAlias = Tuple[Tuple[Statement, ...], Tuple[Var, ...]]
Function : TypeAlias = Tuple[Tuple[Var, ...], "Body"]

ExternalMapping : TypeAlias = Dict[Var, str]
VarNames : TypeAlias = Dict[Optional[int], str]

Program : TypeAlias = Tuple[ExternalMapping, Statement]

def from_epic(p : Tuple[syntax.Statement, Dict[str, Object]]) -> Tuple[Program, VarNames]:
    def do_varlist(l : IList[syntax.Var]) -> IList[Var]:
        if not isinstance(l, tuple):
            assert False, l
        return tuple(do_var(v) for v in l)
    
    def do_var(v : syntax.Var) -> Var:
        if not isinstance(v, syntax.Var):
            assert False, v
        if v.id not in var_names:
            var_names[v.id] = v.name
        assert var_names[v.id] == v.name
        return v.id
    
    def do_func(f : syntax.Function) -> Function:
        return do_varlist(f[0]), do_body(f[1])
    
    def do_body(b : syntax.Body) -> Body:
        return do_stmtlist(b[0]), do_varlist(b[1])
    
    def do_stmtlist(ss : IList[syntax.Statement]) -> IList[Statement]:
        return tuple(do_stmt(s) for s in ss)
    
    def do_stmt(s : syntax.Statement) -> Statement:
        match s:
            case "def", v, f:
                return "def", do_var(v), do_func(f)
            case "call", _call_name, ys, f, xs:
                return "call", do_varlist(ys), do_var(f), do_varlist(xs)
            case "pack", y, xs:
                return "pack", do_var(y), do_varlist(xs)
            case "unpack", ys, x:
                return "unpack", do_varlist(ys), do_var(x)
            case "prim", v, o:
                return "prim", do_var(v), check_pydata(o)
            case "task", _call_name, _xs, _task:
                assert False
            case "loop", _, _, _:
                assert False
    
    external_mapping : ExternalMapping = dict()
    var_names : VarNames = dict()
    for s, o in p[1].items():
        match o:
            case "free", v: pass
            case _: assert False
        i = do_var(v)
        assert i not in external_mapping, (i, external_mapping)
        external_mapping[i] = s

    return (external_mapping, do_stmt(p[0])), var_names

def to_epic(p : Program, var_names : Optional[VarNames]) -> Tuple[syntax.Statement, Dict[str, Object]]:
    def do_varlist(l : IList[Var]) -> IList[syntax.Var]:
        return tuple(do_var(v) for v in l)
    
    def do_var(v : Var) -> syntax.Var:
        if var_names is not None:
            n = var_names[v]
        else:
            n = ""
        return syntax.Var(v, n)
    
    def do_func(f : Function) -> syntax.Function:
        return do_varlist(f[0]), do_body(f[1])
    
    def do_body(b : Body) -> syntax.Body:
        return do_stmtlist(b[0]), do_varlist(b[1])
    
    def do_stmtlist(ss : IList[Statement]) -> IList[syntax.Statement]:
        return tuple(do_stmt(s) for s in ss)
    
    def do_stmt(s : Statement) -> syntax.Statement:
        match s:
            case "def", v, f:
                return "def", do_var(v), do_func(f)
            case "call", ys, f, xs:
                return "call", "", do_varlist(ys), do_var(f), do_varlist(xs)
            case "pack", y, xs:
                return "pack", do_var(y), do_varlist(xs)
            case "unpack", ys, x:
                return "unpack", do_varlist(ys), do_var(x)
            case "prim", v, o:
                return "prim", do_var(v), check_pydata(o)
    
    external_mapping : Dict[str, Object] = dict()
    for i, s in p[0].items():
        assert s not in external_mapping, (i, external_mapping)
        external_mapping[s] = "free", do_var(i)

    return do_stmt(p[1]), external_mapping

def from_python_str(code : str, filename : str = "", lineno : int = 1, translator = translator) -> Tuple[Program, VarNames]:
    func_ast = ast.parse(code, filename=filename, mode='exec', type_comments=True)

    epic = translator.translateToEpic(func_ast, filename, lineno)
    return from_epic(epic)

def from_str(s : str) -> Program:
    p = eval(s)
    typeguard.check_type(p, Program)
    return p

def to_str(p : Program) -> str:
    return pprint.pformat(p)

def stmt_return_vars(s : Statement) -> frozenset[Var]:
    match s:
        case "def", v, f:
            return frozenset({v})
        case "call", ys, f, xs:
            return frozenset(ys)
        case "pack", y, xs:
            return frozenset({y})
        case "unpack", ys, x:
            return frozenset(ys)
        case "prim", v, o:
            return frozenset({v})
    assert False, s

def observe_term_as_value(t : Function) -> object:
    _inps, (stmts, (outp,)) = t
    for stmt in stmts:
        if outp in stmt_return_vars(stmt):
            if stmt[0] == "prim":
                return stmt[2]
            else:
                assert False, f"unsupported: {stmt}"
    assert False
