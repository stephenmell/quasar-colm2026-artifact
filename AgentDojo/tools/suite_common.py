#
#
import inspect
import pydantic
from agentdojo.functions_runtime import _get_dependencies
import types
import enum
import datetime
import agentdojo.default_suites.v1.tools.types as agentdojo_types

from epic import conformal_utils

#
import AgentDojo.custom_translator as translator
from AgentDojo.agentdojo_utils import (
    camel_assistant,
    camel_assistant_conformal,
)

def _bind_env_to_function(env, f):
    env_args = {
        k: v.extract_dep_from_env(env)
        for k, v in _get_dependencies(f).items()
    }
    # This is what we want, but it doesn't handle mixed args and kwargs well
    # return functools.partial(f, **env_args)

    arg_order = tuple(inspect.signature(f).parameters.keys())

    def wrapper(*call_args, **kwargs):
        kwargs_with_deps = kwargs | env_args

        # Often the first argument e.g. `calendar` is passed via "env_args", so we can't just pass the first
        # call_arg straight through or python will complain that `got multiple values for argument 'calendar'`
        # so instead we map call_args to their argument names and then pass everything as a kwarg.
        arg_order_remaining = tuple(filter(lambda p: p not in kwargs_with_deps, arg_order))
        named_args = dict(zip(arg_order_remaining, call_args))
        assert len(call_args) <= len(arg_order_remaining)

        return f(**kwargs_with_deps, **named_args)
    wrapper.__name__ = f.__name__
    return wrapper

import typing
def unwrap(x):
    if type(x) is translator.WrappedCallable:
        return x._unwrap()
    
    type_alias_origin = typing.get_origin(x)
    if type_alias_origin is not None:
        type_alias_args = typing.get_args(x)
        u_origin = unwrap(type_alias_origin)
        u_args = tuple(unwrap(a) for a in type_alias_args)
        return u_origin[u_args]
    return x


def CreateSchema(*args):
    d = {k: (unwrap(v), ...) for k, v in zip(args[::2], args[1::2])}
    return pydantic.create_model("schema", **d, __config__ = {"frozen": True})
    # return pydantic.create_model("schema", **d)

def get_globals_for_env(TOOLS):
    def inner(env, SET, ASYNC=False):
        def collecting_print(*args, **kwargs):
            assert False, (args, kwargs)
        
        def fromisoformat(c, date_str):
            return c.fromisoformat(date_str)
        def isoformat(d):
            return d.isoformat()

        def strptime(_datetime, a1, a2):
            return datetime.datetime.strptime(a1, a2)
        
        def method(name):
            def inner(c, *args, **kwargs):
                return getattr(c, name)(*args, **kwargs)
            inner.__name__ = name
            return inner
            
        ret = {
            ## Built-in types
            "NoneType": types.NoneType,
            "bool": bool,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "tuple": tuple,
            "dict": dict,
            "set": set,

            ## Built-in functions
            "abs": abs,
            "any": any,
            "all": all,
            "bool": bool,
            "dir": dir,
            "divmod": divmod,
            "enumerate": enumerate,
            "float": float,
            "hash": hash,
            "int": int,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "print": print,
            "range": range,
            "repr": repr,
            "reversed": reversed,
            "set": set,
            "sorted": sorted,
            "str": str,
            "tuple": tuple,
            "type": type,
            "zip": zip,
            "sum": sum,

            ## Imported classes
            "ValueError": ValueError,
            "Enum": enum.Enum,
            "datetime": datetime.datetime,
            "timedelta": datetime.timedelta,
            "date": datetime.date,
            "time": datetime.time,
            "timezone": datetime.timezone,
            "BaseModel": pydantic.BaseModel,
            "FieldInfo": pydantic.fields.FieldInfo,
            "EmailStr": pydantic.EmailStr,

            ## Methods
            ".strftime": datetime.datetime.strftime,
            ".strptime": strptime,
            ".keys": dict.keys,
            ".total_seconds": datetime.timedelta.total_seconds,
            ".format": str.format,
            ".strip": str.strip,
            ".weekday": datetime.date.weekday,
            ".fromisoformat": fromisoformat,
            ".isoformat": isoformat,
            ".join": str.join,
            ".lower": str.lower,
            ".split": str.split,
            ".splitlines": str.splitlines,
            ".find": str.find,
            ".combine": method("combine"),
            ".get": method("get"),
            ".model_dump": method("model_dump"),
            ".model_dump_json": method("model_dump_json"),

            ## Tools functions
            **{
                k: _bind_env_to_function(env, v) for k, v in TOOLS.items() if v is not None
            },

            ## Available types
            "CalendarEvent": agentdojo_types.CalendarEvent,
            "EvenStatus": agentdojo_types.EvenStatus,
            "Email": agentdojo_types.Email,
            "EmailStatus": agentdojo_types.EmailStatus,
            "SharingPermission": agentdojo_types.SharingPermission,

            ## Custom
            # "print": collecting_print,
            ## HACKED IN
            "CreateSchema": CreateSchema,
        }
        if SET:
            assert not ASYNC
            ret["query_ai_assistant"] = camel_assistant_conformal.query_ai_assistant

            ret.update({
                "if_stmt": conformal_utils.abstract_if_stmt,
                "for_stmt": conformal_utils.abstract_for_loop,
                "and_expr": conformal_utils.abstract_and_expr,
                "or_expr": conformal_utils.abstract_or_expr,
                "not_expr": conformal_utils.abstract_not_expr,
                "len": conformal_utils.abstract_len,
            })
        else:
            if ASYNC:
                ret["query_ai_assistant"] = camel_assistant.query_ai_assistant_async
            else:
                # ret["query_ai_assistant"] = camel_assistant_conformal.query_ai_assistant
                ret["query_ai_assistant"] = camel_assistant.query_ai_assistant_sync
        return ret
    return inner