import pathlib
from PIL.Image import Image
from dataclasses import dataclass
from typing import Optional, List
import frozendict
from utils import (
    read_json
)

@dataclass
class Context:
    METHODS : any
    MODELS : any
    CALL : any
    MODEL_OUTPUTS : any
    LOCK : int
    CALLS: List[str]
    ROUNDS : any

@dataclass
class WrappedImage:
    image : Image
    filename : str
    CONTEXT : Context

POSSIBLE_OPTIONS = frozendict.deepfreeze(read_json(f"{pathlib.Path(__file__).parent.resolve()}/../vipergpt/possible_options.json"))

def INIT(self, image: Image, left: Optional[int]=None, lower: Optional[int]=None, right:  Optional[int]=None, upper: Optional[int]=None):
    if type(image) == WrappedImage:
        self.filename = image.filename
        self.CONTEXT = image.CONTEXT
        image = image.image

    self.image = image

    if left is None and right is None and upper is None and lower is None:
        self.left = 0
        self.lower = 0
        self.right = image.width
        self.upper = image.height
        self.cropped_image = self.image
    else:
        self.left = int(left)
        self.lower = int(lower)
        self.right = int(right)
        self.upper = int(upper)
        self.cropped_image = self.image.crop((self.left, self.lower, self.right, self.upper))

    self.width = self.right - self.left
    self.height = self.upper - self.lower

    self.horizontal_center = (self.left + self.right) / 2
    self.vertical_center = (self.lower + self.upper) / 2

def crop(self, left: int, lower: int, right: int, upper: int) -> any:
    return ImagePatch(WrappedImage(self.cropped_image, self.filename, self.CONTEXT), left, lower, right, upper)

class ImagePatch:
    possible_options = POSSIBLE_OPTIONS

    __init__ = INIT

    def find(self, object_name: str) -> any:
        return self.CONTEXT.METHODS.find(self, object_name)

    def exists(self, object_name: str) -> bool:
        return self.CONTEXT.METHODS.exists(self, object_name)

    def verify_property(self, object_name: str, attribute: str) -> bool:
        return self.CONTEXT.METHODS.verify_property(self, object_name, attribute)

    def simple_query(self, query: str) -> str:
        return self.CONTEXT.METHODS.simple_query(self, query)

    def best_text_match(self, option_list: list[str], prefix: Optional[str]=None) -> str:
        return self.CONTEXT.METHODS.best_text_match(self, option_list, prefix)

    crop = crop

class ImagePatchAsync:
    possible_options = POSSIBLE_OPTIONS

    __init__ = INIT

    async def find(self, object_name: str) -> any:
        return await self.CONTEXT.METHODS.find(self, object_name)

    async def exists(self, object_name: str) -> bool:
        return await self.CONTEXT.METHODS.exists(self, object_name)

    async def verify_property(self, object_name: str, attribute: str) -> bool:
        return await self.CONTEXT.METHODS.verify_property(self, object_name, attribute)

    async def simple_query(self, query: str) -> str:
        return await self.CONTEXT.METHODS.simple_query(self, query)

    async def best_text_match(self, option_list: list[str], prefix: Optional[str]=None) -> str:
        return await self.CONTEXT.METHODS.best_text_match(self, option_list, prefix)

    crop = crop

def info(self):
    # raise NotImplementedError("this currently doesn't work if there are multiple imagepatches e.g. in video")
    return self.filename, (self.left, self.lower, self.right, self.upper)
