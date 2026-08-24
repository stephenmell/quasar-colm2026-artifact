"""Compile BCP Python programs to EPIC (Quasar) programs.

Derived from upstream BCP/translate_prog.py.  Reads progs_py/<id>.py for every
id in datasets/bcp/indices.json and writes progs_epic/<id>.prog + .varnames.

Usage:
    uv run python translate_bcp.py [--trial N] [-o OUTDIR]

    --trial N   trial dir under datasets/bcp/epic_compiled (default 0)
    -o          where to write progs_epic (default: the in-tree
                datasets/bcp/epic_compiled/<trial>/progs_epic)
"""

import os
import json
import pprint
import argparse

from utils import (
    wrap_expression,
)
from epic import (
    epics_syntax,
)
from AgentDojo import custom_translator

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(HERE, "datasets")

def main():
    parser = argparse.ArgumentParser(description="Compile BCP programs to EPIC.")
    parser.add_argument("--trial", type=int, default=0)
    parser.add_argument("-o", "--output_dir", default=None)
    args = parser.parse_args()
    dataset_dir = os.path.join(DATASETS_DIR, "bcp", "epic_compiled", str(args.trial))

    with open(os.path.join(DATASETS_DIR, "bcp", "indices.json"), "r", encoding="utf-8") as f:
        prog_ids = json.load(f)

    trans_dir = args.output_dir or os.path.join(dataset_dir, "progs_epic")
    os.makedirs(trans_dir, exist_ok=True)

    for problem_id in prog_ids:
        if not os.path.exists(os.path.join(dataset_dir, "progs_py", f"{problem_id}.py")):
            print(f"skipping {problem_id}: no progs_py/{problem_id}.py")
            continue
        with open(os.path.join(dataset_dir, "progs_py", f"{problem_id}.py"), "r") as f:
            prog = f.read()

        prog_wrapped = wrap_expression(prog)
        epics_expr, var_names = epics_syntax.from_python_str(prog_wrapped, "dummy.py", translator = custom_translator)

        trans_filepath = os.path.join(trans_dir, f"{problem_id}.prog")
        varnames_filepath = os.path.join(trans_dir, f"{problem_id}.varnames")
        with open(trans_filepath, "w") as f:
            f.write(epics_syntax.to_str(epics_expr))
        with open(varnames_filepath, "w") as f:
            f.write(pprint.pformat(var_names))

    print(f"compiled {len(prog_ids)} programs to {trans_dir}")

if __name__ == "__main__":
    main()
