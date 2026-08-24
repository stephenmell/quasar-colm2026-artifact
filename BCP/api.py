import types
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

BASE = {
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

    ## Methods
    ".keys": dict.keys,
    ".format": str.format,
    ".strip": str.strip,
    ".join": str.join,
    ".lower": str.lower,
    ".split": str.split,
    ".splitlines": str.splitlines,
    ".find": str.find
}

load_dotenv()
try:
    client_sync = OpenAI()
    client_async = AsyncOpenAI()
except Exception:
    client_sync = None
    client_async = None
MODEL_KWARGS = {
    # "model": "gpt-5",
    "model": "gpt-5-nano",
    "reasoning": {
        "effort": "low",
        # "effort": "medium",
        # "effort": "high",
    },
}
def llm_query_sync(messages):
    # return "FOO"
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    print(">>>")
    print(messages)
    try:
        response = client_sync.responses.create(
            input=messages,
            **MODEL_KWARGS,
        )
    except Exception as e:
        return f"llm_query() error: {e}"

    print(response.output_text)
    print("<<<")
    return response.output_text

async def llm_query_async(messages):
    # return "FOO"
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    print(">>>")
    print(messages)
    try:
        response = await client_async.responses.create(
            input=messages,
            **MODEL_KWARGS,
        )
    except Exception as e:
        return f"llm_query() error: {e}"

    print(response.output_text)
    print("<<<")
    return response.output_text



def get_globals(is_async, return_result, context):
    # replay.wrap_llm_query returns the real function unless a record/replay mode
    # has been set, so the default path is unchanged.
    from BCP import replay
    real = llm_query_async if is_async else llm_query_sync
    return BASE | {
        "llm_query": replay.wrap_llm_query(real, is_async),
        "return_result": return_result,
        "context": context,
    }

NEEDS_STEPPED = {"llm_query"}