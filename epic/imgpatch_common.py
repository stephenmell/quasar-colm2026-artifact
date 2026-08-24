"""Backend-independent perception primitives.

`exists` is defined in terms of `CONTEXT.CALL.simple_query` / `CONTEXT.CALL.find`
rather than any model, so every backend variant shares one copy of it.
Upstream it lives in `imgpatch_local`, and `imgpatch_4o`, `imgpatch_4o_all`,
`imgpatch_conformal` and `imgpatch_replay` all do `exists = imgpatch_local.exists`.
That is only reachable by importing `imgpatch_local`, whose module-level
`import torch` / `from transformers import ...` the replay path must not pay for.

The body below is copied verbatim from `imgpatch_local.exists`.  When
`imgpatch_local.py` is ported (see the porting plan in CLAUDE.md), it should
re-export this rather than keep its own copy.
"""

from .env import *
from word2number import w2n
from .imgpatch import ImagePatch


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
