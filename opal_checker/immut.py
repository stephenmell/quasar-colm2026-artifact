import os
import sys
from typing import Any
import builtins
import ast

#
from opal_checker import (
    immut_dict,
    immut_list,
    immut_set
)

def freeze(o):
    if type(o) is dict:
        return immut_dict.dict({freeze(k): freeze(v) for k, v in o.items()})
    elif type(o) is list:
        raise NotImplementedError("freezing sets")
        return immut_list.list(freeze(o) for x in o)
    elif type(o) is set:
        raise NotImplementedError("freezing sets")
    elif type(o) in {str, int, float}:
        return o
    else:
        raise NotImplementedError(f"{type(o).__name__}")

def wrap_freeze_result(f):
    def wrapped(*args, **kwargs):
        return freeze(f(*args, **kwargs))
    wrapped.__name__ = f.__name__
    return wrapped

class BuiltinOverride:
    stack: list[dict[str, Any]] = []

    def __init__(self, **overrides: Any):
        self.overrides = overrides

    def __enter__(self):
        saved: dict[str, Any] = {}
        for k, v in self.overrides.items():
            saved[k] = builtins.__dict__[k]
            builtins.__dict__[k] = v
        self.stack.append(saved)
        return self

    def __exit__(
        self, _exception_type: Any, _exception_value: Any, _exception_traceback: Any
    ):
        saved = self.stack.pop()
        for k, v in saved.items():
            builtins.__dict__[k] = v
        return False

# IMMUT = BuiltinOverride(dict=immut_dict.dict,list = None, set = None)
GLOBALS = {
    "dict" : immut_dict.dict,
    "list" : immut_list.list,
    "set" : immut_set.set,
}

class LiteralInliner(ast.NodeTransformer):
    def visit_Dict(self, node: ast.Dict):
        return ast.Call(ast.Name(id="dict", ctx=ast.Load()), [node], [])

    def visit_List(self, node: ast.List):
        return ast.Call(ast.Name(id="list", ctx=ast.Load()), [node], [])

    def visit_Set(self, node: ast.Set):
        return ast.Call(ast.Name(id="set", ctx=ast.Load()), [node], [])

    def visit_ListComp(self, node):
        return ast.Call(ast.Name(id="list", ctx=ast.Load()), [node], [])

    def visit_SetComp(self, node):
        return ast.Call(ast.Name(id="set", ctx=ast.Load()), [node], [])

    def visit_DictComp(self, node):
        return ast.Call(ast.Name(id="dict", ctx=ast.Load()), [node], [])

    # def visit_Starred(self, node):
    #     raise NotImplementedError("set literal")


INLINER = LiteralInliner()


def inline_literals(source: str):
    expr = ast.parse(source)
    inlined = INLINER.visit(expr)
    return ast.unparse(inlined)