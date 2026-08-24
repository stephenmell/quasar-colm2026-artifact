import json
import time
import asyncio

CALL_TYPE = "query_ai_assistant"

# "record" | "replay" | None (call the real API and record nothing)
MODE = None

# record: {CALL_TYPE: [(key, result_json, elapsed_ns), ...]}
# replay: {CALL_TYPE: {key: [(result_json, elapsed_ns), ...]}}
MODEL_OUTPUTS = None


def set_mode(mode):
    global MODE
    assert mode in ("record", "replay", None), mode
    MODE = mode


def _key(query, output_schema):
    return json.dumps(
        {"query": query, "schema": output_schema.model_json_schema()},
        sort_keys=True,
    )


def reset_model_outputs():
    global MODEL_OUTPUTS
    MODEL_OUTPUTS = {CALL_TYPE: []}


def save_model_outputs(path):
    with open(path, "w") as f:
        json.dump(MODEL_OUTPUTS, f)


def load_model_outputs(path):
    global MODEL_OUTPUTS
    with open(path, "r") as f:
        lists = json.load(f)

    MODEL_OUTPUTS = {}
    for call_type, entries in lists.items():
        d = {}
        MODEL_OUTPUTS[call_type] = d
        for key, result, elapsed in entries:
            d.setdefault(key, []).append((result, elapsed))


class MissingRecording(KeyError):
    """A replayed program asked for a call that was never recorded."""


def wrap(real_fn, is_async):
    """Return the `query_ai_assistant` the program should see, given MODE."""
    if MODE is None:
        return real_fn

    if MODE == "record":
        if is_async:
            async def recorded(query, output_schema):
                start = time.perf_counter_ns()
                result = await real_fn(query, output_schema)
                elapsed = time.perf_counter_ns() - start
                MODEL_OUTPUTS[CALL_TYPE].append(
                    (_key(query, output_schema), result.model_dump_json(), elapsed))
                return result
        else:
            def recorded(query, output_schema):
                start = time.perf_counter_ns()
                result = real_fn(query, output_schema)
                elapsed = time.perf_counter_ns() - start
                MODEL_OUTPUTS[CALL_TYPE].append(
                    (_key(query, output_schema), result.model_dump_json(), elapsed))
                return result
        return recorded

    def lookup(query, output_schema):
        queue = MODEL_OUTPUTS[CALL_TYPE].get(_key(query, output_schema))
        if queue is None:
            raise MissingRecording(
                f"no recorded {CALL_TYPE} for this (query, schema); the "
                f"recording is incomplete or the program changed since it "
                f"was made"
            )
        if not queue:
            raise MissingRecording(
                f"consumed more {CALL_TYPE} calls for this (query, schema) than "
                f"the recording holds; the engines should demand identical call "
                f"multisets, so this indicates a bug"
            )
        return queue.pop(0)

    if is_async:
        async def replayed(query, output_schema):
            result, elapsed = lookup(query, output_schema)
            await asyncio.sleep(elapsed / 1e9)
            return output_schema.model_validate_json(result)
    else:
        def replayed(query, output_schema):
            result, elapsed = lookup(query, output_schema)
            time.sleep(elapsed / 1e9)
            return output_schema.model_validate_json(result)
    return replayed
