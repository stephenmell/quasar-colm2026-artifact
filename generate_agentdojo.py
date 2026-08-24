"""Generate AgentDojo Python programs from task prompts, via LLM (component 5).

Derived from upstream AgentDojo/pipeline_gen_agentdojo.py.  Nondeterministic:
regenerated programs will not match the committed progs_py.  The committed
programs were produced with --model_name gpt-5 --regenerate checker
--num_attempts 5 (--trial N writes into <suite>_N rather than the bare suite
dir; only the bare dirs, trial 0, ship in datasets/).

Needs OPENAI_API_KEY.
"""

import os
import argparse
from tqdm import tqdm
from agentdojo.task_suite.load_suites import get_suite

from utils import (
    write_file,
    write_json
)
from AgentDojo.agentdojo_utils import (
    gen_prog
)
from AgentDojo.tools import constants

HERE = os.path.dirname(os.path.abspath(__file__))

def parse_args():
    parser = argparse.ArgumentParser(
        description="AgentDojo program generation."
    )
    parser.add_argument(
        "--suites",
        type=str,
        nargs="+",
        default=constants.ALL_SUITES,
        choices=constants.ALL_SUITES,
        help="List of suites to use (default: all)"
    )
    parser.add_argument(
        "-k", "--kind",
        type=str,
        required=True,
        choices=["epic_compiled", "python", "epic_direct"],
        help="Kind of generation"
    )
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="Name of the model to use (e.g., gpt-4o-mini)"
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        default=False,
        help="Whether to rerun and overwrite existing predictions (default: False)"
    )
    parser.add_argument(
        "--regenerate",
        type=str,
        default=None,
        choices=["None", "checker"],
        help="Whether to regenerate programs using the checker (default: None)"
    )
    parser.add_argument(
        "--num_attempts",
        type=int,
        default=1,
        help="Number of regeneration attempts for each example (default: 1)"
    )
    parser.add_argument(
        "--trial",
        type=int,
        default=None,
        help="Which trial"
    )
    parser.add_argument(
        "-o", "--output_dir",
        type=str,
        default=None,
        help="Base datasets directory to write into (default: the in-tree datasets/)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only generate the first N non-example tasks per suite"
    )
    args = parser.parse_args()
    if args.num_attempts < 1:
        parser.error("--num_attempts must be at least 1")
    return args

def main():
    args = parse_args()
    base_dir = args.output_dir or os.path.join(HERE, "datasets")
    dataset_dir = os.path.join(base_dir, "agentdojo", args.model_name)

    for suite_name in args.suites:
        suite_with_trial = suite_name + ("" if args.trial is None else f"_{args.trial}")
        suite_dir = os.path.join(dataset_dir, args.kind, suite_with_trial)
        prog_out_dir = os.path.join(suite_dir, "progs_py")
        os.makedirs(prog_out_dir, exist_ok=True)
            
        suite = get_suite("v1.2.1", suite_name)
        env = suite.load_and_inject_default_environment({})
        exec_globals = constants.SUITE_GLOBALS[suite_name](env, SET=False, ASYNC=False)
        gt_path = os.path.join(
            HERE,
            "AgentDojo",
            "prompts",
            f"{args.kind}_examples",
        )
        print(f"Starting program generation for suite {suite_name} with {len(suite.user_tasks)} tasks...\n")
        n_generated = 0
        for tid, user_task in tqdm(suite.user_tasks.items(), desc=f"Suite {suite_name}"):
            if args.limit is not None and n_generated >= args.limit:
                break
            tid_full = f"{suite.name}_{tid}"
            program_path = os.path.join(prog_out_dir, f"{tid_full}.py")
            times_path = os.path.join(prog_out_dir, f"{tid_full}.json")
            # Exclude example programs in the prompt
            if os.path.isfile(os.path.join(gt_path, f"{tid_full}.py")):
                print(f"Skipping example program: {program_path}")
                continue
            n_generated += 1
            if not args.rerun and os.path.exists(program_path) and os.path.exists(times_path):
                print(f"Skipping existing program: {program_path}")
                continue
            
            progs, times, errors = zip(*gen_prog.genprog_until_translate(args.kind, suite, exec_globals, user_task, args.model_name, args.regenerate, args.num_attempts, args.trial))

            for i, (prog, error) in enumerate(zip(progs, errors)):
                if error is None:
                    write_file(program_path, prog)
                else:
                    fn = program_path + f".{i}"
                    write_file(fn, prog)
                    err_path = fn + ".err"
                    write_file(err_path, error)
            write_json(times_path, {
                "gen_time_s": times,
            })

if __name__ == "__main__":
    main()