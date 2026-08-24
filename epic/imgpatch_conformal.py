import os
from .env import *
import torch
from PIL.Image import Image
from .imgpatch import ImagePatch
from . import imgpatch_local, imgpatch_4o_all
from io import BytesIO
import base64
import re
import json
from .conformal_utils import *

from openai import AsyncOpenAI
import dotenv
dotenv.load_dotenv()

client = None
def initialize_models():
    global client
    # Without a key, cached calls still work; uncached ones fail per-program to .err.
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = AsyncOpenAI(api_key=api_key)
    imgpatch_local.initialize_object()
    imgpatch_local.initialize_clip()















ABSTRACT_EXISTS_UPPER = 0.75
ABSTRACT_EXISTS_LOWER = 0.25
ABSTRACT_FIND_HIGH = 0.5
ABSTRACT_FIND_LOW = 0.1
ABSTRACT_SIMPLE_QUERY_THRESHOLD = 0.5
ABSTRACT_VERIFYPROP_UPPER = 0.75
ABSTRACT_VERIFYPROP_LOWER = 0.25

def image_to_base64(image: Image) -> str:
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")






import hashlib
def _hashstr(string):
    return hashlib.md5(string.encode(), usedforsecurity=False).digest()

CACHE_DIR = None
class ConformalModelCacheConflict(Exception):
    pass
async def _do_model_call(image_b64, query):
    assert CACHE_DIR is not None
    key = _hashstr(image_b64 + query).hex()
    path = f"{CACHE_DIR}/{key}.json"
    if not os.path.exists(path):
        print("CONFORMAL CACHE: not cached, fetching")
        result = await _do_model_call_real(image_b64, query)
        if os.path.exists(path):
            print("CONFORMAL CACHE: WARN: race when writing model call out")
        else:
            with open(path, "w") as f:
                json.dump({"image_b64": image_b64, "query": query, "result": result}, f)
                return result
    else:
        print("CONFORMAL CACHE: reusing cached")

    with open(path, "r") as f:
        j = json.load(f)
    return j["result"]








async def find(self : ImagePatch, object_name: str) -> AbstractTuple[ImagePatch]:
    assert type(object_name) is str
    assert type(self) is ImagePatch

    predictions = imgpatch_local.object_detector(
        self.cropped_image,
        candidate_labels=[object_name],
    )

    bbs_true = [
        (pred['box']['xmin'], pred['box']['ymin'], pred['box']['xmax'], pred['box']['ymax'])
        for pred in predictions if pred['score'] > ABSTRACT_FIND_HIGH
    ]

    bbs_false = [
        (pred['box']['xmin'], pred['box']['ymin'], pred['box']['xmax'], pred['box']['ymax'])
        for pred in predictions if pred['score'] > ABSTRACT_FIND_LOW and pred['score'] <= ABSTRACT_FIND_HIGH
    ]

    return AbstractTuple(tuple(
        [(self.crop(*bb), True) for bb in bbs_true] + [(self.crop(*bb), False) for bb in bbs_false]
    ))

async def _do_model_call_real(image_b64, query):
    if client is None:
        raise RuntimeError("model call not in conformal_cache and OPENAI_API_KEY is not set")
    stream = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    {"type": "text", "text": f"""You are given an image and a question. 
        Your task is to identify *all possible answers* to the question based on the image, 
        and assign a confidence score (between 0 and 1) to each answer. 
        The scores must sum to 1. For each possibility, keep the description concise---no explanation.

        Return your answer in the following JSON format:
        [
        {{ "answer": "ANSWER_1", "score": 0.65 }},
        {{ "answer": "ANSWER_2", "score": 0.35 }}
        ]

        Now, answer the question: \"{query}\""""}
                ]}
            ],
            temperature=0,
        )
    return stream.choices[0].message.content

async def _abstract_simple_query_inner(self : ImagePatch, query: str):
    image_b64 = image_to_base64(self.cropped_image)
    answer = await _do_model_call(image_b64, query)
    # from the answer, extract the answers and the confidence scores
    # Extract JSON block using regex or fallback to parsing entire content
    try:
        json_text = re.search(r'\[\s*{.*?}\s*\]', answer, re.DOTALL).group(0)
        result =json.loads(json_text)
    except:
        raise ValueError("Could not extract a valid JSON answer from the model's response.")
    return result

async def simple_query(self : ImagePatch, query: str) -> AbstractOther[str]:
    result = await _abstract_simple_query_inner(self, query)
    print(result)
    answers = frozenset(item['answer'] for item in result if item['score'] > ABSTRACT_SIMPLE_QUERY_THRESHOLD)
    return AbstractOther(answers)

def _parse_yesno_confidence(response):
    assert len(response) <= 2, f"_parse_yesno_confidence() parse error: {response}"
    yes_score = 0.0
    no_score = 0.0
    for j in response:
        answer = j["answer"].strip().lower()
        if answer == "yes":
            yes_score = j["score"]
        if answer == "no":
            no_score = j["score"]
    assert yes_score + no_score == 1, f"_parse_yesno_confidence() parse error: {response}"
    return yes_score

async def verify_property(image_patch, object_name: str, attribute: str) -> AbstractOther[bool]:
    result = await _abstract_simple_query_inner(image_patch, f'Does the "{object_name} in the image have attribute "{attribute}" (yes/no)?')
    score = _parse_yesno_confidence(result)
    print(result, score)
    if score >= ABSTRACT_VERIFYPROP_UPPER:
        is_yes = ABS_BOOL_TRUE
    elif score >= ABSTRACT_VERIFYPROP_LOWER:
        is_yes = ABS_BOOL_TOP
    else:
        is_yes = ABS_BOOL_FALSE
    return is_yes

async def _abstract_exists_get_patch_score(object_name : str, patch : ImagePatch) -> float:
    response = await _abstract_simple_query_inner(patch, f"Is this a {object_name}?")
    return _parse_yesno_confidence(response)

async def best_text_match(image_patch, option_list: list[str], prefix: Optional[str] = None) -> str:
    assert False, "best_text_match not implemented"

async def exists(self : ImagePatch, object_name: str) -> AbstractOther[bool]:
    # Check if the object refers to a number
    if object_name.isdigit() or object_name.lower().startswith("number"):
        assert False

    # Check generic object existence
    patches = await imgpatch_4o_all.find(self, object_name)
    ret = ABS_BOOL_FALSE
    for patch in patches:
        score = await _abstract_exists_get_patch_score(object_name, patch)
        if score >= ABSTRACT_EXISTS_UPPER:
            is_yes = ABS_BOOL_TRUE
        elif score >= ABSTRACT_EXISTS_LOWER:
            is_yes = ABS_BOOL_TOP
        else:
            is_yes = ABS_BOOL_FALSE
        ret |= is_yes
        if get_abstract_bool_value(ret) == True:
            break

    return ret
