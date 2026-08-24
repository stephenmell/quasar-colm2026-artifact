"""Replay recorded BCP executions under Quasar or plain Python semantics.

BCP's single model entry point (`llm_query`, gpt-5-nano) is served from
recordings/<id>.json by BCP.replay, which also sleeps each call's recorded
latency -- so like GQA, the measured wall-clock reflects how the engine
schedules the recorded latencies, and no API key is needed for --replay.

Inputs, per trial dir datasets/bcp/epic_compiled/<trial>/:
    progs_py/<id>.py, progs_epic/<id>.prog + .varnames, recordings/<id>.json
plus datasets/bcp/problems.jsonl -- the 80 sampled rows of the BCP corpus
(upstream reads the full 2.0 GB decrypted.jsonl; the artifact ships only the
sampled subset, extracted by extract_bcp_problems.py).

Usage:
    uv run python run_bcp.py (-e | -p) [--replay | --record] [options]

    -e / -p            engine: EPIC (Quasar) or plain Python
    --replay           serve llm_query from recordings, sleeping recorded
                       latencies (how the shipped results were produced)
    --record           run live against the API (needs OPENAI_API_KEY) and
                       write recordings
    --trial N          trial dir under datasets/bcp/epic_compiled (default 0)
    --rounds           also record per-execution interaction counts
    -o, --output_dir   base directory for outputs, laid out like the shipped
                       trial dir: <out>/exec_<engine>[_rounds][_replay]/ and
                       <out>/rounds/<engine>/.  Default: the in-tree trial
                       dir, i.e. overwrite what the artifact ships.
    --limit N          only process the first N programs, in sorted order
"""

import os
import json
import argparse
import time
import traceback

import typeguard
from tqdm import tqdm

from epic import (
    semantics,
    syntax,
    epics_syntax,
    printing,
    epics_vipergpt,
)
from utils import (
    get_filepaths_from_dirs,
    read_file,
    write_file,
    write_json,
)
from AgentDojo.agentdojo_utils import run
from AgentDojo import custom_translator
import BCP.api
import BCP.replay

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(HERE, "datasets")
PROBLEMS_PATH = os.path.join(DATASETS_DIR, "bcp", "problems.jsonl")

def parse_args():
    parser = argparse.ArgumentParser(
        description="BCP program execution."
    )
    parser.add_argument(
        "-k", "--kind",
        type=str,
        default="epic_compiled",
        choices=["epic_compiled"],
        help="Kind of generation (default: epic_compiled)"
    )
    parser.add_argument(
        "--trial",
        type=int,
        default=0,
        help="Which trial (default: 0)"
    )
    parser.add_argument(
        "-o", "--output_dir",
        type=str,
        default=None,
        help="Base output directory (default: in-tree, overwriting shipped results)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--epic', help='Run using EPIC', action='store_true', default=False)
    group.add_argument('-p', '--python', help='Run using Python', action='store_true', default=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--record",
        action="store_true",
        default=False,
        help="Record calls for replay (live API run)"
    )
    group.add_argument(
        "--replay",
        action="store_true",
        default=False,
        help="Replay recorded calls"
    )
    parser.add_argument(
        "--rounds",
        action="store_true",
        default=False,
        help="Count rounds"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N programs, in sorted order"
    )
    return parser.parse_args()

def log_error(err_filepath, err, stage, msg=""):
    error_report = (
        f"Stage: {stage}\n"
        f"Error: {str(err)}\n"
        f"Traceback: {msg}\n"
        f"{''.join(traceback.format_exception(err))}"
    )
    try:
        write_file(err_filepath, error_report)
    except Exception as e:
        print(f"Failed to log error: {e}")

def get_bcp_problem(idx):
    with open(PROBLEMS_PATH, "r", encoding="utf-8") as fout:
        for line in fout.readlines():
            row = json.loads(line)
            if row['query_id'] == str(idx):
                documents = row['gold_docs'] + row['evidence_docs'] + row['negative_docs']
                context = tuple(d["text"] for d in sorted(documents, key=lambda d: int(d["docid"])))
                return (
                    row['query'],
                    row['answer'],
                    context,
                    tuple(d['text'] for d in row['gold_docs']),
                    tuple(d['text'] for d in row['negative_docs']),
                    tuple(d['text'] for d in row['evidence_docs']),
                )
    assert False

def main():
    args = parse_args()
    dataset_dir = os.path.join(DATASETS_DIR, "bcp")
    kind_dir = os.path.join(dataset_dir, args.kind, str(args.trial))

    EPIC = args.epic
    SYNC = not EPIC

    RECORD = args.record
    REPLAY = args.replay
    ROUNDS = args.rounds

    out_dir = args.output_dir or kind_dir
    suffix = f"{'epic' if EPIC else 'py'}"
    EVAL_DIRNAME = os.path.join(out_dir, f"exec_{suffix}{'_rounds' if ROUNDS else ''}{'_replay' if REPLAY else ''}")
    RECORD_DIRNAME = os.path.join(kind_dir, "recordings")
    ROUNDS_DIRNAME = os.path.join(out_dir, "rounds", suffix)

    if RECORD or REPLAY:
        BCP.replay.set_mode("record" if RECORD else "replay")
    if REPLAY and not os.path.exists(RECORD_DIRNAME):
        print(f"ERROR: Replay directory {RECORD_DIRNAME} does not exist.")
        return
    os.makedirs(EVAL_DIRNAME, exist_ok=True)
    if RECORD:
        os.makedirs(RECORD_DIRNAME, exist_ok=True)
    if ROUNDS:
        os.makedirs(ROUNDS_DIRNAME, exist_ok=True)

    if EPIC:
        filepaths = get_filepaths_from_dirs([os.path.join(kind_dir, "progs_epic")], extension=".prog")
    else:
        filepaths = get_filepaths_from_dirs([os.path.join(kind_dir, "progs_py")], extension=".py")
    filepaths = sorted(filepaths)
    if args.limit is not None:
        filepaths = filepaths[:args.limit]

    print(f"Starting program execution with {len(filepaths)} programs...\n")
    CONTEXT = run.Context(
        LOCK=0,
        CALLS=0,
        ROUNDS=[],
    )
    for fn_path in tqdm(filepaths, desc="Executing"):
        filename = os.path.basename(fn_path)
        print(f"\nProcessing: {fn_path}")
        tid_full = os.path.splitext(filename)[0]
        prog_id = int(tid_full)

        _query, answer, context, gold_d, negative_d, evidence_d = get_bcp_problem(prog_id)

        run_result = None
        def return_result(res):
            nonlocal run_result
            assert run_result is None
            run_result = res

        if EPIC:
            exec_globals = BCP.api.get_globals(True, return_result, context)
            mappings = {
                k: run.make_stepped(custom_translator, custom_translator.wrap(v), CONTEXT)
                if ROUNDS and k in BCP.api.NEEDS_STEPPED
                else custom_translator.wrap(v)
                for k, v in exec_globals.items()
            }
        else:
            exec_globals = BCP.api.get_globals(False, return_result, context)

        exec_filepath = os.path.join(EVAL_DIRNAME, f"{tid_full}.json")
        lock_filepath = os.path.join(EVAL_DIRNAME, f"{tid_full}.lock")
        err_filepath = os.path.join(EVAL_DIRNAME, f"{tid_full}.err")
        if os.path.exists(exec_filepath) or os.path.exists(err_filepath) or os.path.exists(lock_filepath):
            print(f"\tSkipping {filename} (already processed)")
            continue

        with open(lock_filepath, "w"): pass

        if RECORD or REPLAY:
            model_outputs_filepath = os.path.join(RECORD_DIRNAME, f"{tid_full}.json")
        if ROUNDS:
            rounds_filepath = os.path.join(ROUNDS_DIRNAME, f"{tid_full}.json")

        def clear_existing():
            traceback.print_exc()
            if RECORD:
                # A partial recording is worse than none: it would replay as a
                # missing-call error later, so drop it with the failed result.
                try:
                    os.remove(model_outputs_filepath)
                except FileNotFoundError:
                    pass
            try:
                os.remove(exec_filepath)
            except FileNotFoundError:
                pass

            if ROUNDS:
                try:
                    os.remove(rounds_filepath)
                except FileNotFoundError:
                    pass
            os.remove(lock_filepath)

        try:
            if EPIC:
                syntax._symbol_next_id = 10000 #HACK: Should find highest var in AST
                try:
                    epics_expr = epics_syntax.from_str(read_file(fn_path))
                except FileNotFoundError as e:
                    log_error(err_filepath, e, "epics_syntax.from_str")
                    print("\tSkipping due to missing translation.")
                    clear_existing()
                    continue
                try:
                    with open(os.path.join(os.path.dirname(fn_path), f"{tid_full}.varnames"), "r") as f:
                        varnames = eval(f.read())
                        typeguard.check_type(varnames, epics_syntax.VarNames)
                except FileNotFoundError as e:
                    log_error(err_filepath, e, "typeguard.check_type")
                    print("\tNo varnames found for EPIC. Debugging may be harder.")
                    varnames = None

                try:
                    epic_term = epics_vipergpt.finalize(epics_expr, [], mappings, varnames, translator = custom_translator)
                except Exception as e:
                    log_error(err_filepath, e, "epics_vipergpt.finalize")
                    print("\tIgnoring due to translation failure.")
                    clear_existing()
                    continue
            else:
                code = read_file(fn_path)

            if RECORD:
                BCP.replay.reset_model_outputs()
            elif REPLAY:
                try:
                    BCP.replay.load_model_outputs(model_outputs_filepath)
                except FileNotFoundError as e:
                    log_error(err_filepath, e, "BCP.replay.load_model_outputs")
                    print("\tSkipping due to missing recording.")
                    clear_existing()
                    continue

            if ROUNDS:
                CONTEXT.ROUNDS = []

            if EPIC:
                try:
                    start = time.perf_counter_ns()
                    printing.print_func(epic_term)
                    print("\tEVALUATING...")
                    epic_exec_trace = tuple(semantics.reduce_graph_opportunistic(epic_term))
                    epic_exec_result = epic_exec_trace[-1]
                    elapsed = time.perf_counter_ns() - start
                except Exception as e:
                    log_error(err_filepath, e, "semantics.reduce_graph_opportunistic")
                    print("\tIgnoring due to eval failure.")
                    clear_existing()
                    continue

                try:
                    print(f"\tDONE after {len(epic_exec_trace)} steps.")
                    printing.print_func(epic_exec_result)
                    assert run_result is not None
                except Exception as e:
                    log_error(err_filepath, e, "epics_syntax.observe_term_as_value")
                    print("\tUnable to find result")
                    clear_existing()
                    continue
            else:
                exec_locals = {}
                start = time.perf_counter_ns()
                try:
                    exec(code, exec_globals)
                    assert run_result is not None
                except Exception as e:
                    log_error(err_filepath, e, "agentdojo_eval.exec_with_return")
                    print(f"\tAgentDojo execution failed: {e}")
                    clear_existing()
                    continue
                elapsed = time.perf_counter_ns() - start
        except Exception as e:
            log_error(err_filepath, e, "other execution error")
            print(f"\tExecution failed: {e}")
            clear_existing()
            continue

        is_correct = str(run_result).lower().strip() == answer.lower().strip()

        write_json(exec_filepath, {
            "result": str(run_result),
            "time_ns": elapsed,
            "correct": is_correct,
            "ground_truth": answer,
        })
        if RECORD:
            BCP.replay.save_model_outputs(model_outputs_filepath)
        if ROUNDS:
            write_json(rounds_filepath, CONTEXT.ROUNDS)
        os.remove(lock_filepath)

        print(f"\tExecution completed in {elapsed / 1e6:.2f} ms")
        print(f"\tExecution output: {str(run_result)}")
        print(f"\tExecution correct: {is_correct}")
        if not is_correct:
            print(f"\tExecution GT: {answer}")
        print()

    print(f"\n✅ Finished processing {len(filepaths)} programs. Results saved to {EVAL_DIRNAME}.")

if __name__ == "__main__":
    main()
