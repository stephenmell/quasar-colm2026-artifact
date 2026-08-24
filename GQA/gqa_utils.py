import random
import datasets
from pathlib import Path
import re

from utils import (
    read_json,
)

def load_gqa(split: str, n: int, seed: int = 2025):
    dataset_images = datasets.load_dataset("lmms-lab/GQA", f"{split}_all_images", split=split)
    dataset_instructions = datasets.load_dataset("lmms-lab/GQA", f"{split}_all_instructions", split=split)
    image_mappings = {item["id"]: item["image"] for item in dataset_images}
    random.seed(seed)
    indices = random.sample(range(len(dataset_instructions)), n)
    return image_mappings, dataset_instructions, indices

def load_gqa_images(split: str):
    dataset_images = datasets.load_dataset("lmms-lab/GQA", f"{split}_all_images", split=split)
    image_mappings = {item["id"]: item["image"] for item in dataset_images}
    return image_mappings

def create_items_path(split: str, n: int, seed: int):
    return f"{split}_n{n}_seed{seed}.json"

def parse_items_path(dataset_dir: str):
    d = Path(dataset_dir)
    if not d.is_dir():
        raise NotADirectoryError(f"Not a directory: {dataset_dir}")
    json_files = sorted(f for f in d.glob("*.json") if f.is_file())
    if not json_files:
        raise FileNotFoundError(f"No items file found in directory: {dataset_dir}")
    if len(json_files) > 1:
        names = ", ".join(f.name for f in json_files)
        raise RuntimeError(f"Expected exactly one items file, found {len(json_files)}: {names}")
    items = read_json(json_files[0])
    items_filename = json_files[0].stem
    m = re.match(r"(?P<split>[a-zA-Z0-9]+)_n(?P<num>\d+)_seed(?P<seed>\d+)", items_filename)
    if not m:
        raise ValueError(f"Invalid items filename format: {items_filename}")
    return {
        "split": m.group("split"),
        "num_samples": int(m.group("num")),
        "seed": int(m.group("seed")),
    }, items
