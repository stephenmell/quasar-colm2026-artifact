#
#
import importlib
import asyncio
import types
import frozendict
import json

#
from epic import (
    graph_semantics,
    imgpatch,
    #
    epics_vipergpt,
    #
    conformal_utils,
)
#
#
#

#
#
#
#
#
#
#

def proxy(methods, wrapper, CONTEXT):
    proxied = types.SimpleNamespace()
    proxied.find = wrapper(methods.find, CONTEXT)
    proxied.verify_property = wrapper(methods.verify_property, CONTEXT)
    proxied.simple_query = wrapper(methods.simple_query, CONTEXT)
    proxied.best_text_match = wrapper(methods.best_text_match, CONTEXT)
    proxied.exists = wrapper(methods.exists, CONTEXT)
    # proxied.select_answer = wrapper(methods.select_answer, CONTEXT)
    return proxied

def make_sync(function, CONTEXT=None):
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(function(*args, **kwargs))
    wrapper.__name__ = function.__name__
    return wrapper

def make_stepped(function, CONTEXT):
    async def wrapper(*args, **kwargs):
        CONTEXT.CALLS.append(function.__name__)
        lock = CONTEXT.LOCK
        await graph_semantics.REDUCTION_STUCK_EVENT.wait()
        if CONTEXT.LOCK == lock:
            CONTEXT.LOCK += 1
            CONTEXT.ROUNDS.append(CONTEXT.CALLS)
            CONTEXT.CALLS = []
        return await function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    return wrapper

def make_context(models, recording, sync, track_rounds=False) -> imgpatch.Context:
    models.initialize_models()
    methods = importlib.import_module("epic.imgpatch_record") if recording else models
    call = methods
    CONTEXT = imgpatch.Context(
        MODELS=models,
        METHODS=None,
        CALL=call,
        MODEL_OUTPUTS=None,
        LOCK=0,
        CALLS=[],
        ROUNDS=[],
    )
    if track_rounds:
        methods = proxy(methods, make_stepped, CONTEXT)
    if sync:
        methods = proxy(methods, make_sync, CONTEXT)
    CONTEXT.METHODS = methods
    return CONTEXT

TIME_CLOSE_THRESH = 0.9
def load_model_outputs(path, CONTEXT):
    MODEL_OUTPUTS = {}
    with open(path, "r") as f:
        model_outputs_lists = json.load(f)

    model_outputs_lists = frozendict.deepfreeze(model_outputs_lists)

    for call_type, l in model_outputs_lists.items():
        d = {}
        MODEL_OUTPUTS[call_type] = d
        for x, y, t in l:
            if x in d:
                y2, t2 = d[x]
                print(f"WARN: duplicate for {call_type} {x}, {y} {t} vs {y2} {t2}")
                assert y == y2
                if not (t/t2 >= TIME_CLOSE_THRESH and t2/t >= TIME_CLOSE_THRESH):
                    print("WARN: significant time mismatch", t/t2)
            d[x] = (y, t)

    CONTEXT.MODEL_OUTPUTS = MODEL_OUTPUTS

def reset_model_outputs(CONTEXT):
    CONTEXT.MODEL_OUTPUTS = {
        "find": [],
        "verify_property": [],
        "simple_query": [],
        "best_text_match": [],
    }

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

def concrete_and_expr(left, right):
    return left and right

def concrete_or_expr(left, right):
    return left or right

def concrete_not_expr(operand):
    return not operand

def get_py_exec_command(py_code, filename, CONTEXT, ASYNC=False, SET=False):
    exec_globals = {
        "__builtins__": __builtins__,
        "ImagePatch": imgpatch.ImagePatchAsync if ASYNC else imgpatch.ImagePatch,
        #
        **({
            "bool_to_yesno": epics_vipergpt.bool_to_yesno,
            # "if_stmt": concrete_if_stmt,
            # "for_stmt": concrete_for_loop,
            # "and_expr": concrete_and_expr,
            # "or_expr": concrete_or_expr,
            # "not_expr": concrete_not_expr,
            # "len": len,
        } if not SET else {}),
        **({
            "bool_to_yesno": conformal_utils.abstract_bool_to_yesno,
            "if_stmt": conformal_utils.abstract_if_stmt,
            "for_stmt": conformal_utils.abstract_for_loop,
            "and_expr": conformal_utils.abstract_and_expr,
            "or_expr": conformal_utils.abstract_or_expr,
            "not_expr": conformal_utils.abstract_not_expr,
            "len": conformal_utils.abstract_len,
        } if SET else {}),
    }

    code = compile(py_code, filename=filename, mode='exec')
    exec_locals = {}
    exec(code, exec_globals, exec_locals)

    return exec_locals.get("execute_command")
