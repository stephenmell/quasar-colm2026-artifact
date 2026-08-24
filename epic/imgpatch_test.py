from .env import *
import random
import hashlib
import numpy as np

SLEEP_TIME = 1.0

def initialize_models():
    pass

def hashstr(string):
    return hashlib.md5(string.encode(), usedforsecurity=False).digest()

async def find(self, object_name: str) -> list:
    await asyncio.sleep(SLEEP_TIME)
    patches = []
    rand = random.Random((self.left + self.lower + self.right + self.upper).to_bytes(4, byteorder="big") + hashstr(object_name))
    for i in range(rand.randint(0, 4)):
        left = rand.randint(self.left, self.right)
        lower = rand.randint(self.lower, self.upper)
        right = rand.randint(left, self.right)
        upper = rand.randint(lower, self.upper)
        patches.append(self.crop(left, lower, right, upper))
    return patches

async def exists(self, object_name: str) -> bool:
    await asyncio.sleep(SLEEP_TIME)
    return not random.Random((self.left + self.lower + self.right + self.upper).to_bytes(4, byteorder="big") + hashstr(object_name)).randint(0, 1)

async def verify_property(self, object_name: str, attribute: str) -> bool:
    return np.array([not random.Random((self.left + self.lower + self.right + self.upper).to_bytes(4, byteorder="big") + hashstr(object_name) + hashstr(attribute)).randint(0, 1)])

async def simple_query(self, query: str) -> str:
    return query

async def best_text_match(self, option_list: list[str], prefix: str=None) -> str:
    seed = (self.left + self.lower + self.right + self.upper).to_bytes(4, byteorder="big")
    if prefix != None:
        seed += hashstr(prefix)
    for option in option_list:
        seed += hashstr(option)
    return option_list[random.Random(seed).randrange(0, len(option_list))]

# VideoSegment functions
async def select_answer(self, info_formatting: str, question: str, options=None) -> str:
    await asyncio.sleep(SLEEP_TIME)
    return question
