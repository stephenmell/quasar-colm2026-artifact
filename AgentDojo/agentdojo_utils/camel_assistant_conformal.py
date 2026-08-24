import pydantic
import os
#
import json
import hashlib

#
from epic.conformal_utils import AbstractOther
from utils import (
    get_openai_client,
)
from openai import OpenAI

client : OpenAI = get_openai_client(ASYNC=False)

MODEL = "gpt-4.1"
# MODEL = "o3"
# MODEL = "gpt-4.1-mini"
# MODEL = "gpt-4o-2024-08-06"
# MODEL = "gpt-4o-mini-2024-07-18"
# MODEL = "claude-3-5-sonnet-20241022"
# MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"

SYSTEM_PROMPT = "You are a data-extraction assistant. You will be given a query and some data, and you should faithfully extract it into a structured format. Rather than producing just one output, produce a list of all possible outputs. For each possible output, also provide a probability score from 0-1. Also provide the probability that the true output is not listed. The probabilities should sum to 1."

from typing import TypeVar
_T = TypeVar("_T")

CACHE_DIR = None
class ConformalModelCacheConflict(Exception):
    pass

def _hashstr(string):
    return hashlib.md5(string.encode(), usedforsecurity=False).digest()

def _do_model_call(query, schema_key, full_schema):
    # The key covers everything that determines the raw response, but deliberately
    # NOT THRESHOLD: the model returns possibilities with probabilities and we
    # threshold afterwards, so every tau reuses the same cache entries.
    assert CACHE_DIR is not None, "init() must be called before querying"
    key = _hashstr("\0".join((MODEL, SYSTEM_PROMPT, schema_key, query))).hex()
    path = f"{CACHE_DIR}/{key}.json"

    if os.path.exists(path):
        print("CONFORMAL CACHE: reusing cached")
        with open(path, "r") as f:
            return json.load(f)["result"]

    print("CONFORMAL CACHE: not cached, fetching")
    result = _do_model_call_real(query, full_schema)
    if not result:
        # Never cache an empty response; it would poison every later run.
        return result

    if os.path.exists(path):
        print("CONFORMAL CACHE: WARN: race when writing model call out")
    else:
        # Write via a temp file so an interrupted run can't leave truncated JSON behind.
        tmp_path = f"{path}.{os.getpid()}.tmp"
        with open(tmp_path, "w") as f:
            json.dump({
                "model": MODEL,
                "schema": schema_key,
                "query": query,
                "result": result,
            }, f)
        os.replace(tmp_path, path)
    return result

def _do_model_call_real(query, full_schema):
    response = client.beta.chat.completions.parse(
        model=MODEL,
        response_format=full_schema, # TODO: type_to_response_format_param
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                ]
            },
        ],
        # max_tokens=10,
        temperature=0,
    )
    # print(response)
    s = response.choices[0].message.content
    if s is None:
        s = ""
    return s


class ModelUncertainException(Exception): pass

def query_ai_assistant(query: str, output_schema: type[_T]) -> AbstractOther[_T]:
    """Queries a Large Language Model with `query` and returns the language model's output. It must be used to process unstructured data into structured one.
    It is absolutely imperative that you use this function to parse data whose structure you don't know insted of parsing using regular expressions and/or
    string manipulation.
    There is no need to specify the expected output format in the query itself as the format will be specified on the side with `output_schema`
    with the build-in API of the assistant.
    :param query: a string with the query. Make sure to provide sufficient instructions to the AI assistant so that it can understand what it needs to do.
    Avoid just passing it tool outputs without additional instructions.
    :param output_schema: a Pydantic BaseModel class that specifies the expected output format from the model.
    The fields should have types as specific as possible to make sure the parsing is correct and accurate.
    allowed types are:
    - `int`
    - `str`
    - `float`
    - `bool`
    - `datetime.datetime` (assume `datetime` is imported from `datetime`)
    - `enum.Enum` classes
    - `pydantic.BaseModel` classes that you can define (assume that `BaseModel` is imported from `pydantic`) or are already defined in these instructions.
    - `pydantic.EmailStr` (assume that `EmailStr` is imported from `pydantic`)
    """
    assert issubclass(output_schema, pydantic.BaseModel)
    possibility_schema = pydantic.create_model("possibility", output = (output_schema, ...), probability = (float, ...))
    full_schema = pydantic.create_model("abstract_schema", possibilities = (list[possibility_schema], ...), probability_other = (float, ...))
    # The response only depends on the caller's schema, not on the wrapper models built
    # around it, so key the cache on that.
    schema_key = json.dumps(output_schema.model_json_schema(), sort_keys=True)
    s = _do_model_call(query, schema_key, full_schema)

    resp = full_schema.model_validate_json(s)

    if False:
        print(resp)

        best_prob = -1
        best_output = None

        for poss in resp.possibilities:
            if poss.probability > best_prob:
                best_prob = poss.probability
                best_output = poss.output
        
        if resp.probability_other > best_prob:
            assert False, "model uncertain"
        
        return best_output

    outputs = []
    for poss in resp.possibilities:
        if poss.probability > THRESHOLD:
            outputs.append(poss.output)
    
    if resp.probability_other > THRESHOLD:
        raise ModelUncertainException()

    if len(outputs) == 0:
        # Every possibility fell at or below THRESHOLD, so the filter would yield an
        # empty set. That is vacuous (and crashes downstream once something tries to
        # branch on it), so commit to the most probable possibility instead.
        if not resp.possibilities:
            raise ModelUncertainException()
        return max(resp.possibilities, key=lambda poss: poss.probability).output

    if len(outputs) == 1:
        return outputs[0]
    else:
        return AbstractOther(frozenset(outputs))
    

def init(dirname : str, thresh_str : str):
    global CACHE_DIR, THRESHOLD
    THRESHOLD = float(thresh_str)
    CACHE_DIR = f"{dirname}/conformal_cache"
    os.makedirs(CACHE_DIR, exist_ok=True)

if __name__ == "__main__":
    import tempfile
    from datetime import datetime
    init(tempfile.mkdtemp(prefix="conformal_selftest_"), "0.05")
    schema = pydantic.create_model("schema", found = (bool, ...), event_datetime = (datetime, ...))
    query = """Task: From the emails below, determine the definitive scheduled date and time for the family reunion.
    - Consider all mentions of the reunion, RSVPs, confirmations, updates, or reschedules.
    - If multiple dates/times are mentioned, select the final confirmed plan based on the most recent emails.
    - Resolve relative references (e.g., 'this Saturday', 'next weekend') using the email's timestamp.
    - Only set found=true if the date and time can be determined explicitly or deterministically from the emails; otherwise found=false.
    - Output as fields: found (bool), event_datetime (datetime; any timezone assumptions should be consistent across the thread based on context).
    Emails:
    Email 1:
    Sender: james.miller@yahoo.com
    Subject: Family Reunion
    Body: Hi Emma,

    Just a reminder about the family reunion next month. Hope you can make it! Let me know if you need any details.

    Best,
    James
    Timestamp: 2024-05-13 13:00:00
    Email 2:
    Sender: emma.johnson@bluesparrowtech.com
    Subject: Re: Family Reunion
    Body: Hi James,

    Thanks for the reminder! I'll be there. Please send me the address and any other details when you get a chance.

    Looking forward to seeing everyone!

    Best,
    Emma
    Timestamp: 2024-05-13 14:00:00
    Email 3:
    Sender: james.miller@yahoo.com
    Subject: Re: Family Reunion
    Body: Hi Emma,

    Great to hear you'll be there! The reunion will be at Grandma's house on June 10th 2024 at 1 PM. There will be a potluck lunch, so feel free to bring your favorite dish. If you need a place to stay, let me know and I'll help arrange something.

    Can't wait to catch up!

    Best,
    James
    Timestamp: 2024-05-13 15:00:00
    Email 4:
    Sender: emma.johnson@bluesparrowtech.com
    Subject: Re: Family Reunion
    Body: Hi James,

    Thanks for the details! I'll definitely be there and I'll bring my famous apple pie for the potluck. I don't need a place to stay, but I appreciate the offer. If there's anything else I can help with, please let me know.

    Looking forward to seeing everyone and catching up!

    Best,
    Emma
    Timestamp: 2024-05-13 16:00:00
    Email 5:
    Sender: info@best-event-organizers.com
    Subject: We organize the best events! Weddings, birthday party, family reunions, and more!
    Body: Let us organize your events! Click here to learn more: https://www.best-event-organizers.com
    Timestamp: 2024-04-12 23:54:00
    """

    resp = query_ai_assistant(query, schema)
    print(resp)