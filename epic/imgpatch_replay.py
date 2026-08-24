from .env import *
from PIL.Image import Image
from .imgpatch import ImagePatch
from . import imgpatch, imgpatch_common
import asyncio

NANOSEC = 1000**3

def initialize_models():
    pass

async def find(self : ImagePatch, object_name: str) -> IList[ImagePatch]:
    bbs, t = self.CONTEXT.MODEL_OUTPUTS["find"][(imgpatch.info(self), object_name)]
    await asyncio.sleep(t/NANOSEC)
    return tuple(
        self.crop(*bb)
        for bb in bbs
    )

async def verify_property(self : ImagePatch, object_name: str, attribute: str) -> bool:
    res, t = self.CONTEXT.MODEL_OUTPUTS["verify_property"][(imgpatch.info(self), object_name, attribute)]
    await asyncio.sleep(t/NANOSEC)
    return res

async def simple_query(self : ImagePatch, query: str) -> str:
    answer, t = self.CONTEXT.MODEL_OUTPUTS["simple_query"][(imgpatch.info(self), query)]
    await asyncio.sleep(t/NANOSEC)
    return answer

async def best_text_match(self : ImagePatch, option_list: list[str], prefix: Optional[str] = None) -> str:
    ret, t = self.CONTEXT.MODEL_OUTPUTS["best_text_match"][(imgpatch.info(self), tuple(option_list), prefix)]
    await asyncio.sleep(t/NANOSEC)
    return ret

exists = imgpatch_common.exists

async def select_answer(self, info_formatting: str, question: str, options=None) -> str:
    ret, t = self.CONTEXT.MODEL_OUTPUTS["select_answer"][(imgpatch.info(self), info_formatting, question, options)]
    await asyncio.sleep(t/NANOSEC)
    return ret