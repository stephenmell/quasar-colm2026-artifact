from .env import *
from PIL.Image import Image
from .imgpatch import ImagePatch
from . import imgpatch, imgpatch_local
import time
import torch

async def find(self: ImagePatch, object_name: str) -> IList[ImagePatch]:
    start = time.perf_counter_ns()
    patches = await self.CONTEXT.MODELS.find(self, object_name)
    elapsed = time.perf_counter_ns() - start
    bbs = [
        (patch.left, patch.lower, patch.right, patch.upper)
        for patch in patches
    ]
    for bb in bbs:
        for x in bb:
            assert type(x) is int, (type(x), x)
    self.CONTEXT.MODEL_OUTPUTS["find"].append((
        (imgpatch.info(self), object_name),
        bbs,
        elapsed,
    ))
    return patches

async def verify_property(self: ImagePatch, object_name: str, attribute: str) -> bool:
    start = time.perf_counter_ns()
    res = await self.CONTEXT.MODELS.verify_property(self, object_name, attribute)
    if type(res) == torch.Tensor:
        res = res.item()
    elapsed = time.perf_counter_ns() - start
    self.CONTEXT.MODEL_OUTPUTS["verify_property"].append((
        (imgpatch.info(self), object_name, attribute),
        res,
        elapsed,
    ))
    return res

async def simple_query(self: ImagePatch, query: str) -> str:
    start = time.perf_counter_ns()
    answer = await self.CONTEXT.MODELS.simple_query(self, query)
    elapsed = time.perf_counter_ns() - start
    self.CONTEXT.MODEL_OUTPUTS["simple_query"].append(((imgpatch.info(self), query), answer, elapsed))
    return answer

async def best_text_match(self : ImagePatch, option_list: list[str], prefix: Optional[str] = None) -> str:
    start = time.perf_counter_ns()
    ret = await self.CONTEXT.MODELS.best_text_match(self, option_list, prefix)
    elapsed = time.perf_counter_ns() - start
    self.CONTEXT.MODEL_OUTPUTS["best_text_match"].append(((imgpatch.info(self), option_list, prefix), ret, elapsed))
    return ret

exists = imgpatch_local.exists