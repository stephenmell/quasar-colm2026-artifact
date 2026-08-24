import os
from .env import *
import torch
from PIL.Image import Image
from .imgpatch import ImagePatch
from . import imgpatch_local
from io import BytesIO
import base64

from openai import AsyncOpenAI
from concurrent_openai import ConcurrentOpenAI, ConcurrentCompletionResponse
import dotenv
dotenv.load_dotenv()

client = None
def initialize_models():
    global client
    client = ConcurrentOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        max_concurrent_requests=8,
    )
    # client = AsyncOpenAI(
    #     api_key=os.getenv("OPENAI_API_KEY"),
    # )
    imgpatch_local.initialize_object()
    imgpatch_local.initialize_clip()

async def do_gpt_call(**kwargs) -> ConcurrentCompletionResponse:
    # model, messages, max_tokens, temperature
    # return client.chat.completions.create(**kwargs)
    return await client.create(**kwargs)

THRESH_OBJ_DET = 0.125

def image_to_base64(image: Image) -> str:
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

async def find(self : ImagePatch, object_name: str) -> IList[ImagePatch]:
    predictions = imgpatch_local.object_detector(
        self.cropped_image,
        candidate_labels=[object_name],
    )
    bbs = [
        (pred['box']['xmin'], pred['box']['ymin'], pred['box']['xmax'], pred['box']['ymax'])
        for pred in predictions if pred['score'] > THRESH_OBJ_DET
    ]
    return tuple(
        self.crop(*bb)
        for bb in bbs
    )
async def verify_property(image_patch, object_name: str, attribute: str) -> bool:
    image_b64 = image_to_base64(image_patch.cropped_image)
    prompt = f"""
You are given an image of a {object_name}. Determine whether the attribute "{attribute}" applies to the object in the image. 
Answer with "Yes" or "No".
"""
    # Call GPT-4o with the image and the prompt
    response = await do_gpt_call(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful vision-language assistant."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]
            }
        ],
        max_tokens=10,
        temperature=0
    )

    answer = response.content.strip().lower()
    return "yes" in answer

async def best_text_match(image_patch, option_list: list[str], prefix: Optional[str] = None) -> str:
    image_b64 = image_to_base64(image_patch.cropped_image)

    # Build prompt options
    if prefix is not None:
        option_list_to_use = [f"{prefix} {opt}" for opt in option_list]
    else:
        option_list_to_use = option_list

    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(option_list_to_use)])
    
    prompt = f"""You are given an image and a list of possible descriptions. 
Choose the option that best matches the content of the image.
Return only the number of the best option.

Options:
{options_text}
"""

    response = await do_gpt_call(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for image classification."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]
            }
        ],
        max_tokens=5,
        temperature=0
    )

    reply = response.content.strip()

    # Extract selected index
    try:
        selected_index = int(reply.split()[0]) - 1
        return option_list[selected_index]
    except (ValueError, IndexError):
        raise ValueError(f"Could not parse GPT-4o response: '{reply}'")

async def simple_query(self : ImagePatch, query: str) -> str:
    image_b64 = image_to_base64(self.cropped_image)
    stream = await do_gpt_call(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                {"type": "text", "text": f"{query} Respond with a short answer only — no explanation."}
            ]}
        ],
        temperature=0,
    )
    answer = stream.content
    if answer is None:
        answer = ""
    return answer

exists = imgpatch_local.exists

VIDEO_QUESTION_PATH = os.path.join(os.path.dirname(__file__), f"../prompts/video_question.txt")
# VideoSegment functions
async def select_answer(self, info_formatting: str, question: str, options=None) -> str:
    def format_dict(x):
        if isinstance(x, dict):
            x = ''.join([f'\n\t- {k}: {format_dict(v)}' for k, v in x.items()])
        return x
    with open(VIDEO_QUESTION_PATH, 'r') as f:
        prompt = f.read()
    # info_formatting = '\n'.join([f"- {k}: {format_dict(v)}" for k, v in info.items()])
    prompt = prompt.format(info=info_formatting, question=question, options=options)
    # answer = self.forward('gpt3_general', prompt)
    # answer = answer.strip()
    stream = await do_gpt_call(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ]
            }
        ],
        temperature=0,
    )
    answer = stream.content
    if answer is None:
        answer = ""
    return answer