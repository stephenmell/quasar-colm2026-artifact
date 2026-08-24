from .env import *
import torch
from transformers import pipeline, AutoProcessor, AutoModelForVision2Seq, CLIPProcessor, CLIPModel
from word2number import w2n
from .imgpatch import ImagePatch

# TORCH_DEVICE = "cuda:6"
TORCH_DEVICE = "cpu"

THRESH_CLIP = 0.5
THRESH_OBJ_DET = 0.5

object_detector = None
def initialize_object():
    global object_detector
    # load the zero-shot object object detector
    object_detector = pipeline(model="google/owlv2-base-patch16-ensemble", task='zero-shot-object-detection', device=TORCH_DEVICE)

vision_processor = None
vision_model = None
def initialize_vision():
    global vision_processor, vision_model
    # load the vision-language model
    vision_processor = AutoProcessor.from_pretrained('HuggingFaceTB/SmolVLM-Instruct')
    vision_model = AutoModelForVision2Seq.from_pretrained('HuggingFaceTB/SmolVLM-Instruct', torch_dtype=torch.bfloat16, _attn_implementation="flash_attention_2" ).to(TORCH_DEVICE)

clip_processor = None
clip_model = None
def initialize_clip():
    global clip_processor, clip_model
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(TORCH_DEVICE)

def initialize_models():
    print("fixme cuda device hardcoded to", TORCH_DEVICE)
    initialize_object()
    initialize_vision()
    initialize_clip()

async def find(self : ImagePatch, object_name: str) -> IList[ImagePatch]:
    predictions = object_detector(
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

async def verify_property(self : ImagePatch, object_name: str, attribute: str) -> bool:
    name = f"{attribute} {object_name}"
    negative_categories = [f"{att} {object_name}" for att in self.possible_options['attributes']]
    inputs = clip_processor(text=[name]+negative_categories, images=self.cropped_image, return_tensors="pt", padding=True).to(TORCH_DEVICE)
    outputs = clip_model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1)
    res = probs[0, 0] > THRESH_CLIP
    return res

async def simple_query(self : ImagePatch, query: str) -> str:
    messages = [
        {"role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": f"{query} Respond with a short answer only — no explanation."}
            ]}
    ]
    prompt = vision_processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = vision_processor(text=prompt, images=self.cropped_image, return_tensors="pt").to(TORCH_DEVICE)
    generated_ids = vision_model.generate(**inputs, max_new_tokens=16, do_sample=False)
    generated_text = vision_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    if "Assistant:" in generated_text:
        answer = generated_text.split("Assistant:")[-1].strip()
    else:
        answer = generated_text.strip()

    answer = answer.strip(".").strip()
    return answer

async def best_text_match(self : ImagePatch, option_list: list[str], prefix: Optional[str] = None) -> str:
    option_list_to_use = option_list
    if prefix is not None:
        option_list_to_use = [prefix + " " + option for option in option_list]
    inputs = clip_processor(text=option_list_to_use, images=self.cropped_image, return_tensors="pt", padding=True).to(TORCH_DEVICE)
    outputs = clip_model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1)
    selected = probs[0].argmax()
    return option_list[selected]


async def exists(self : ImagePatch, object_name: str) -> bool:
    # Check if the object refers to a number
    if object_name.isdigit() or object_name.lower().startswith("number"):
        object_name = object_name.lower().replace("number", "").strip()
        if len(object_name) > 0:
            try:
                expected = w2n.word_to_num(object_name)
            except ValueError:
                print(f"[Warning] Cannot convert '{object_name}' to number.")
                return False

            answer = await self.CONTEXT.CALL.simple_query(self, "What number is written in the image (in digits)?")
            try:
                predicted = w2n.word_to_num(answer)
                return predicted == expected
            except ValueError:
                print(f"[Warning] Model returned non-numeric answer: '{answer}'")
                return False

    # Check generic object existence
    patches = await self.CONTEXT.CALL.find(self, object_name)
    filtered_patches = []
    for patch in patches:
        response = (await self.CONTEXT.CALL.simple_query(patch, f"Is this a {object_name}?")).strip().lower()
        if "yes" in response:
            filtered_patches.append(patch)

    return len(filtered_patches) > 0

# VideoSegment functions
async def select_answer(self, info_formatting: str, question: str, options=None) -> str:
    def format_dict(x):
        if isinstance(x, dict):
            x = ''.join([f'\n\t- {k}: {format_dict(v)}' for k, v in x.items()])
        return x
    with open("/home/bzhang16/conformal_viper/prompts/video_question.txt", 'r') as f:
        prompt = f.read()
    # info_formatting = '\n'.join([f"- {k}: {format_dict(v)}" for k, v in info.items()])
    prompt = prompt.format(info=info_formatting, question=question, options=options)
    # answer = self.forward('gpt3_general', prompt)
    # answer = answer.strip()
    
    # TODO