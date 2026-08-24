import os
import sys
import time
import asyncio
import random
import hashlib
import frozendict

from .env import *
from . import translator, syntax, epics_syntax, imgpatch

def bool_to_yesno(bool_answer: bool) -> str:
    return "yes" if bool_answer else "no"

def strip_names(f : syntax.Function) -> syntax.Function:
    def do_varlist(l : IList[syntax.Var]) -> IList[syntax.Var]:
        if not isinstance(l, tuple):
            assert False, l
        return tuple(do_var(v) for v in l)

    def do_var(v : syntax.Var) -> syntax.Var:
        return syntax.Var(v.id, "v")

    def do_func(f : syntax.Function) -> syntax.Function:
        return do_varlist(f[0]), do_body(f[1])

    def do_body(b : syntax.Body) -> syntax.Body:
        return do_stmtlist(b[0]), do_varlist(b[1])

    def do_stmtlist(ss : IList[syntax.Statement]) -> IList[syntax.Statement]:
        return tuple(do_stmt(s) for s in ss)

    def do_stmt(s : syntax.Statement) -> syntax.Statement:
        match s:
            case "def", v, f:
                return "def", do_var(v), do_func(f)
            case "call", _call_name, ys, f, xs:
                return "call", "", do_varlist(ys), do_var(f), do_varlist(xs)
            case "pack", y, xs:
                return "pack", do_var(y), do_varlist(xs)
            case "unpack", ys, x:
                return "unpack", do_varlist(ys), do_var(x)
            case "prim", v, o:
                return "prim", do_var(v), o
            case "task", _call_name, _xs, _task:
                assert False
            case "loop", _, _, _:
                assert False

    return do_func(f)

def make_mappings(calls, translator = translator):
    return {
        **{
            k: translator.wrap(v)
            for k, v in {
                "str": str,
                "int": int,
                "float": int,
                "set": int,
                ".lower": str.lower,
                ".upper": str.upper,
                "max": max,
                "min": min,
                "abs": abs,
                "bool_to_yesno": bool_to_yesno,
                "ImagePatch": imgpatch.ImagePatch,
                ".exists": calls.exists,
                ".simple_query": calls.simple_query,
                ".verify_property": calls.verify_property,
                ".best_text_match": calls.best_text_match,
                ".crop": imgpatch.crop,
                # ".select_answer": calls.select_answer,
            }.items()
        },
        **{
            k: translator.wrap(v, TO_CHURCH=True)
            for k, v in {
                "range": range,
                ".find": calls.find,
            }.items()
        },
    }

def finalize(epics_prog : epics_syntax.Program, args, mappings, varnames : Optional[epics_syntax.VarNames], translator = translator) -> syntax.Function:
    epic_prog = epics_syntax.to_epic(epics_prog, varnames)
    epic_expr = translator.translationFinalize(epic_prog, args, mappings)
    f_with_names = syntax.as_function(epic_expr)
    return f_with_names
    # return strip_names(f_with_names)
