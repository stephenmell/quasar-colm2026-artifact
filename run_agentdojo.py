"""Run recorded AgentDojo programs under Quasar or plain Python semantics.

The suite tool APIs (`agentdojo` package, pinned suite version v1.2.1) are
deterministic; the one live-LLM seam is `query_ai_assistant` (`gpt-4.1`,
temperature 0), which 71 of the 93 programs call.  `--record` runs it live
(needs `OPENAI_API_KEY`) and writes `recordings/<id>.json`; `--replay` serves
it from those recordings via `AgentDojo.agentdojo_utils.assistant_replay`,
sleeping each call's recorded latency, so no key is needed and `time_ns`
reflects how the engine schedules the recorded latencies (like GQA and BCP).
With neither flag the call is live and nothing is recorded; without a key
those programs produce a `.err` and everything else still reproduces.

The shipped `exec_py_replay/` and `exec_epic_replay/` results are replay runs
of the shipped `recordings/` (recorded 2026-08-20 under `-p`; `exec_py/` is
the live control run that produced them, which py replay reproduces exactly).
Record and replay under the same `PYTHONHASHSEED` -- some queries interpolate
set-ordered lists, and the recording key embeds the query.  One epic caveat:
a program whose query embeds tool state that an earlier tool call mutates can
issue a different query under Quasar's scheduling than the sequential
recording captured; `banking_user_task_9` does, so it gets a
missing-recording `.err` under `-e --replay` even though live epic runs
succeed on it.

Usage:
    uv run python run_agentdojo.py --suite SUITE (-e | -p | -s) [options]

    --suite            workspace | travel | slack | banking
    --trial N          use suite dir <suite>_N instead of the bare suite dir
                       (trial 0, the only generation shipped in datasets/)
    -e / -p / -s       engine: EPIC (Quasar), plain Python, or set-valued
                       (conformal) Python
    -t TAU             conformal threshold (required with -s); outputs go to
                       conformal_exec/<tau>/.  Model calls are served from the
                       shipped conformal_cache/, so no API key is needed as
                       long as every call is cached (trial 0 fully is).
                       Incompatible with --record/--replay: the conformal
                       assistant has its own cache.
    --record           run query_ai_assistant live and write recordings, into
                       <out>/recordings/<id>.json
    --replay           serve query_ai_assistant from <out>/recordings/,
                       sleeping recorded latencies; also appends _replay to
                       the output dir name (the shipped form)
    --rounds           also record per-execution interaction counts, into
                       rounds/<engine>/; also appends _rounds to the exec dir
                       name (like BCP), because round tracking perturbs time_ns
    -o, --output_dir   base directory for outputs, laid out like the shipped
                       suite dir: <out>/exec_<engine>[_rounds][_replay]/<id>.{json,err}
                       and <out>/rounds/<engine>/<id>.json.  Default: the
                       in-tree suite dir, i.e. overwrite what the artifact
                       ships.
    --limit N          only process the first N programs, in sorted order
"""

import os
import argparse
import time
import traceback

import typeguard
import inspect
from tqdm import tqdm
from agentdojo.task_suite.load_suites import get_suite

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
from AgentDojo.tools import (
    constants,
    suite_common,
)
from AgentDojo.agentdojo_utils import (
    eval as agentdojo_eval,
    run,
    camel_assistant_conformal,
    assistant_replay,
)
from AgentDojo import custom_translator

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(HERE, "datasets")

def parse_args():
    parser = argparse.ArgumentParser(
        description="AgentDojo program execution."
    )
    parser.add_argument(
        "--dataset_dir",
        type=str,
        default="agentdojo/gpt-5",
        help="Dataset directory under datasets/ (default: agentdojo/gpt-5)"
    )
    parser.add_argument(
        "-k", "--kind",
        type=str,
        default="epic_compiled",
        choices=["epic_compiled"],
        help="Kind of generation (default: epic_compiled)"
    )
    parser.add_argument(
        "--suite",
        type=str,
        default="workspace",
        choices=["workspace", "travel", "slack", "banking"],
        help="Suite to use (default: workspace)"
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
        help="Base output directory (default: in-tree, overwriting shipped results)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--epic', help='Run using EPIC', action='store_true', default=False)
    group.add_argument('-p', '--python', help='Run using Python', action='store_true', default=False)
    group.add_argument('-s', '--set', help='Run using conformal semantics', action='store_true', default=False)
    parser.add_argument(
        '-t', '--conformal_thresh',
        help="Conformal threshold tau (required with -s)"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--record",
        action="store_true",
        default=False,
        help="Record query_ai_assistant calls for replay (live API run)"
    )
    group.add_argument(
        "--replay",
        action="store_true",
        default=False,
        help="Replay recorded query_ai_assistant calls; appends _replay to the output dir name"
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

def main():
    args = parse_args()
    dataset_dir = os.path.join(DATASETS_DIR, args.dataset_dir)
    suite_with_trial = args.suite + ("" if args.trial is None else f"_{args.trial}")
    kind_dir = os.path.join(dataset_dir, args.kind, suite_with_trial)

    EPIC = args.epic
    SET = args.set
    SYNC = not EPIC

    RECORD = args.record
    REPLAY = args.replay
    ROUNDS = args.rounds
    assert not (SET and (RECORD or REPLAY)), "--record/--replay are incompatible with -s"

    out_dir = args.output_dir or kind_dir
    suffix = f"{'epic' if EPIC else 'py'}"
    if not SET:
        EVAL_DIRNAME = os.path.join(out_dir, f"exec_{suffix}{'_rounds' if ROUNDS else ''}{'_replay' if REPLAY else ''}")
    else:
        assert args.conformal_thresh is not None, "--conformal_thresh must be specified"
        camel_assistant_conformal.init(kind_dir, args.conformal_thresh)
        EVAL_DIRNAME = os.path.join(out_dir, "conformal_exec", args.conformal_thresh)
    RECORD_DIRNAME = os.path.join(out_dir, "recordings")
    ROUNDS_DIRNAME = os.path.join(out_dir, "rounds", suffix)

    if RECORD or REPLAY:
        assistant_replay.set_mode("record" if RECORD else "replay")
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
    elif SET:
        filepaths = get_filepaths_from_dirs([os.path.join(kind_dir, "progs_set")], extension=".prog")
    else:
        filepaths = get_filepaths_from_dirs([os.path.join(kind_dir, "progs_py")], extension=".py")
    filepaths = sorted(filepaths)
    if args.limit is not None:
        filepaths = filepaths[:args.limit]

    print(f"Starting program execution for suite {args.suite} with {len(filepaths)} programs...\n")
    CONTEXT = run.Context(
        LOCK=0,
        CALLS=0,
        ROUNDS=[],
    )
    suite_name = args.suite
    suite = get_suite("v1.2.1", suite_name)
    for fn_path in tqdm(filepaths, desc="Executing"):
        filename = os.path.basename(fn_path)
        print(f"\nProcessing: {fn_path}")
        tid_full = os.path.splitext(filename)[0]
        tid = tid_full.replace(f"{suite.name}_", "")

        user_task = suite.user_tasks[tid]
        env = suite.load_and_inject_default_environment({})
        task_environment = user_task.init_environment(env)
        pre_environment = task_environment.model_copy(deep=True)

        tool_apis = constants.TOOL_APIS[suite_name]
        exec_globals = suite_common.get_globals_for_env(tool_apis.TOOLS)(env, SET=SET, ASYNC=not SYNC)
        if not SET:
            exec_globals["query_ai_assistant"] = assistant_replay.wrap(
                exec_globals["query_ai_assistant"], is_async=not SYNC)
        if EPIC:
            mappings = {
                k: run.make_stepped(custom_translator, custom_translator.wrap(v), CONTEXT)
                if ROUNDS and k in tool_apis.TOOLS.keys()
                else custom_translator.wrap(v)
                for k, v in exec_globals.items()
            }

        exec_filepath = os.path.join(EVAL_DIRNAME, f"{tid_full}.json")
        err_filepath = os.path.join(EVAL_DIRNAME, f"{tid_full}.err")
        if os.path.exists(exec_filepath) or os.path.exists(err_filepath):
            print(f"\tSkipping {filename} (already processed)")
            continue

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
                assistant_replay.reset_model_outputs()
            elif REPLAY:
                try:
                    assistant_replay.load_model_outputs(model_outputs_filepath)
                except FileNotFoundError as e:
                    log_error(err_filepath, e, "assistant_replay.load_model_outputs")
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
                    epic_exec_result_value = epics_syntax.observe_term_as_value(epic_exec_result)
                    exec_result = epic_exec_result_value
                except Exception as e:
                    log_error(err_filepath, e, "epics_syntax.observe_term_as_value")
                    print("\tUnable to find result")
                    clear_existing()
                    continue
            else:
                exec_locals = {}
                start = time.perf_counter_ns()
                try:
                    if SET:
                        comp = compile(code, filename=filename, mode='exec')
                        exec_locals = {}
                        exec(comp, exec_globals, exec_locals)

                        try:
                            exec_result = exec_locals.get("execute_command")()
                        except camel_assistant_conformal.ModelUncertainException:
                            exec_result = "__MODEL_UNCERTAIN__"
                    else:
                        exec_result = agentdojo_eval.exec_with_return(code, exec_globals, exec_locals)
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

        print(f"Evaluating and saving result: {filename}")
        post_environment = task_environment.model_copy(deep=True)
        try:
            utility = user_task.utility(
                model_output=str(exec_result),
                pre_environment=pre_environment,
                post_environment=post_environment,
            )
        except NotImplementedError as e:
            err_msg = "Utility for function calls not implemented."
            log_error(err_filepath, e, "utility", msg=err_msg)
            print(f"\t{err_msg}")
            clear_existing()
            continue

        write_json(exec_filepath, {
            "result": str(exec_result),
            "time_ns": elapsed,
            "utility": utility
        })
        if RECORD:
            assistant_replay.save_model_outputs(model_outputs_filepath)
        if ROUNDS:
            write_json(rounds_filepath, CONTEXT.ROUNDS)

        print(f"\tExecution completed in {elapsed / 1e6:.2f} ms")
        print(f"\tExecution output: {str(exec_result)}")
        print(f"\tExecution utility: {utility}")
        if not utility:
            print(f"\tExecution GT: {inspect.getsource(user_task.utility)}")
        print()

    print(f"\n✅ Finished processing {len(filepaths)} programs. Results saved to {EVAL_DIRNAME}.")

if __name__ == "__main__":
    main()
