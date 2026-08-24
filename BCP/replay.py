import json
import time
import asyncio

CALL_TYPE = "llm_query"

# "record" | "replay" | None (call the real API and record nothing)
MODE = None

# record: {CALL_TYPE: [(key, result, elapsed_ns), ...]}
# replay: {CALL_TYPE: {key: (result, elapsed_ns)}}
MODEL_OUTPUTS = None

# Ratio below which two recorded durations for the same key are worth warning
# about; matches TIME_CLOSE_THRESH in eval/run_utils.py.
TIME_CLOSE_THRESH = 0.9


def set_mode(mode):
    global MODE
    assert mode in ("record", "replay", None), mode
    MODE = mode


def _key(messages):
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    return json.dumps(messages, sort_keys=True)


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


def wrap_llm_query(real_fn, is_async):
    """Return the `llm_query` the program should see, given the current MODE."""
    if MODE is None:
        return real_fn

    if MODE == "record":
        if is_async:
            async def recorded(messages):
                start = time.perf_counter_ns()
                result = await real_fn(messages)
                elapsed = time.perf_counter_ns() - start
                MODEL_OUTPUTS[CALL_TYPE].append((_key(messages), result, elapsed))
                return result
        else:
            def recorded(messages):
                start = time.perf_counter_ns()
                result = real_fn(messages)
                elapsed = time.perf_counter_ns() - start
                MODEL_OUTPUTS[CALL_TYPE].append((_key(messages), result, elapsed))
                return result
        return recorded

    # MODE == "replay": consume the next recorded response for this prompt and
    # re-impose its original latency.
    def lookup(messages):
        queue = MODEL_OUTPUTS[CALL_TYPE].get(_key(messages))
        if queue is None:
            raise MissingRecording(
                f"no recorded {CALL_TYPE} for this prompt; the recording is "
                f"incomplete or the program changed since it was made"
            )
        if not queue:
            raise MissingRecording(
                f"consumed more {CALL_TYPE} calls for this prompt than the "
                f"recording holds; the engines should demand identical call "
                f"multisets, so this indicates a bug"
            )
        return queue.pop(0)

    if is_async:
        async def replayed(messages):
            result, elapsed = lookup(messages)
            await asyncio.sleep(elapsed / 1e9)
            return result
    else:
        def replayed(messages):
            result, elapsed = lookup(messages)
            time.sleep(elapsed / 1e9)
            return result
    return replayed
