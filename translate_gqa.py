"""Compile GQA Python programs to EPIC (Quasar) programs.

Derived from upstream GQA/pipeline_translate.py.  Reads progs_py/<id>.prog and
writes progs_epic/<id>.prog + <id>.varnames (and info_compilation/<id>.json
with the compile time) through epic/translator.py -- the default translator,
not AgentDojo's.  Deterministic; regenerates the shipped progs_epic exactly.

Usage:
    uv run python translate_gqa.py [-o OUTDIR] [--limit N]

    -o, --output_dir   base directory for progs_epic/ and info_compilation/
                       (default: the in-tree datasets/gqa_val/gpt-5/epic_compiled,
                       i.e. overwrite what the artifact ships)
    --limit N          only the first N programs, in sorted order

Existing outputs are skipped, upstream-style, so pre-create <id>.prog files to
restrict a run.
"""

import os
import argparse
import time
import traceback
import pprint

from tqdm import tqdm

from epic import (
    imgpatch_test,
    epics_syntax,
)
from eval import (
    run_utils,
)
from utils import (
    read_file,
    write_file,
    write_json,
    get_filepaths_from_dirs,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(HERE, "datasets")

def parse_args():
    parser = argparse.ArgumentParser(
        description="GQA program translation."
    )
    parser.add_argument(
        "--dataset_dir",
        type=str,
        default="gqa_val/gpt-5",
        help="Dataset directory under datasets/ (default: gqa_val/gpt-5)"
    )
    parser.add_argument(
        "-k", "--kind",
        type=str,
        default="epic_compiled",
        choices=["epic_compiled"],
        help="Kind of generation (default: epic_compiled)"
    )
    parser.add_argument(
        "-o", "--output_dir",
        type=str,
        default=None,
        help="Base output directory (default: in-tree, overwriting shipped programs)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N programs, in sorted order"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    kind_dir = os.path.join(DATASETS_DIR, args.dataset_dir, args.kind)
    out_dir = args.output_dir or kind_dir
    trans_dir = os.path.join(out_dir, "progs_epic")
    meta_dir = os.path.join(out_dir, "info_compilation")
    os.makedirs(trans_dir, exist_ok=True)
    os.makedirs(meta_dir, exist_ok=True)

    py_filepaths = sorted(get_filepaths_from_dirs([os.path.join(kind_dir, "progs_py")], extension=".prog"))
    if args.limit is not None:
        py_filepaths = py_filepaths[:args.limit]
    print(f"Starting translation of {len(py_filepaths)} programs from {kind_dir} ...")
    CONTEXT = run_utils.make_context(imgpatch_test, False, False)
    succ = 0
    fail = 0
    for fn_path in tqdm(py_filepaths, desc="Translating"):
        filename = os.path.basename(fn_path)
        print(f"Processing: {filename}")
        filename_no_ext = os.path.splitext(filename)[0]

        trans_filepath = os.path.join(trans_dir, f"{filename_no_ext}.prog")
        varnames_filepath = os.path.join(trans_dir, f"{filename_no_ext}.varnames")
        err_filepath = os.path.join(trans_dir, f"{filename_no_ext}.err")
        meta_filepath = os.path.join(meta_dir, f"{filename_no_ext}.json")

        if os.path.exists(trans_filepath) or os.path.exists(err_filepath):
            print(f"\tSkipping {filename} (already processed)")
            continue

        py_code = read_file(fn_path)
        try:
            execute_command = run_utils.get_py_exec_command(py_code, filename, CONTEXT)
            if execute_command is None:
                print(f"\tSkipping {filename} (no execute_command found)")
                continue

            print(f"\tTranslating {filename} to EPIC ...")
            symbol_next_id = epics_syntax.syntax._symbol_next_id
            start = time.perf_counter_ns()
            epics_expr, var_names = epics_syntax.from_python_str(py_code, fn_path)
            elapsed = time.perf_counter_ns() - start
            write_file(trans_filepath, epics_syntax.to_str(epics_expr))
            write_file(varnames_filepath, pprint.pformat(var_names))
            write_json(meta_filepath, {"time_ns": elapsed})

            print(f"\tSuccessfully translated and saved {filename}.")
            succ += 1
            try:
                os.remove(err_filepath)
            except FileNotFoundError:
                pass
        except Exception as e:
            print(f"\tFailed to translate {filename} to EPIC: {e}")
            write_file(err_filepath, "\n".join(traceback.format_exception(e)))
            fail += 1
            traceback.print_exc()
            try:
                os.remove(meta_filepath)
            except FileNotFoundError:
                pass
            try:
                os.remove(trans_filepath)
            except FileNotFoundError:
                pass
        finally:
            epics_syntax.syntax._symbol_next_id = symbol_next_id
    print(f"\n✅ Translation complete: \n{succ + fail} out of {len(py_filepaths)} processed\n{succ} succeeded\n{fail} failed")

if __name__ == "__main__":
    main()
