"""Replay recorded GQA executions under Quasar or plain Python semantics.

Reads compiled programs (``progs_epic/`` for -e, ``progs_py/`` for -p) and the
recorded perception-model outputs from ``recordings/<variant>/``, re-runs each
program, and writes ``<id>.json`` on success or ``<id>.err`` on failure.  No API
keys and no perception models are needed: every model call is served from the
recording, sleeping for the recorded latency, so the measured wall-clock
reflects how the engine schedules those latencies -- Quasar overlaps them,
Python pays them sequentially, which is the speedup the paper reports.

The GQA images themselves *are* still needed -- ``ImagePatch`` crops real pixels
even when the answers come from the recording -- so the first run downloads
``lmms-lab/GQA`` (``val_all_images``) via HuggingFace ``datasets``.

Usage:
    uv run python run_gqa.py (-e | -p | -s -t TAU) [--record] [-o OUTDIR] [--rounds] [--limit N] [--ids FILE]

    -e / -p            engine: EPIC (Quasar) or plain Python
    --record           run live instead of replaying: perception from the
                       4o_all backend (OWLv2/CLIP locally + gpt-4o-mini; needs
                       OPENAI_API_KEY and `uv sync --extra record`), writing
                       recordings/<variant>/ instead of exec results.  Both
                       engines demand the same calls (opportunistic evaluation
                       reorders work but never runs past a guard), and the
                       recordings are dict-keyed, so either engine's recording
                       serves both replay engines; -e is the convention the
                       shipped recordings used.  (BCP's recordings are ordered
                       FIFOs instead and must be recorded with -p -- see
                       run_bcp.py.)
    -o, --output_dir   Base directory for outputs, laid out exactly like the
                       shipped dataset:
                           <out>/exec/<variant>_<engine>_replay[_rounds]/<id>.{json,err}
                           <out>/rounds/<variant>_<engine>/<id>.json
                       Default: datasets/<dataset_dir>/<kind>, i.e. overwrite what
                       the artifact ships.  Point this at /tmp to verify against
                       the committed results without destroying them.
    --rounds           Also record per-execution interaction-round counts (what
                       the interaction heatmaps in gen_figs_opportunistic.py
                       consume).  Note this perturbs "time_ns": round tracking
                       synchronises model calls, which is why upstream keeps
                       these runs in a separate exec/ directory.
    --limit N          Only process the first N programs, in sorted order.
    --ids FILE         Only run the programs whose ids are in FILE (a JSON list),
                       applied before --limit.  The shipped conformal_ids.json
                       lists the 500-program population of the paper's conformal
                       experiment, whose model calls the shipped conformal_cache
                       fully covers -- so `-s -t TAU --ids .../conformal_ids.json`
                       needs no API key and leaves the tree untouched.

Existing outputs are skipped, so a run can be interrupted and resumed.  Results
are byte-identical to the committed ones except for the "time_ns" field, which is
measured wall-clock and varies by well under 1% between runs.
"""

import os
import argparse
import json
import time
import traceback

import typeguard
from tqdm import tqdm

from GQA.gqa_utils import (
    load_gqa_images,
    parse_items_path,
)
from epic import (
    imgpatch,
    imgpatch_replay,
    syntax,
    epics_syntax,
    semantics,
    epics_vipergpt,
)
from eval import (
    run_utils,
)
from utils import (
    get_filepaths_from_dirs,
    read_file,
    write_file,
    write_json,
)

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(HERE, "datasets")

VARIANT = "4o_all"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Replay recorded GQA executions under Quasar (EPIC) or Python semantics."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--epic', help='Run using EPIC', action='store_true', default=False)
    group.add_argument('-p', '--python', help='Run using Python', action='store_true', default=False)
    group.add_argument('-s', '--set', help='Run using Set Python', action='store_true', default=False)
    parser.add_argument(
        '-t', '--conformal_thresh',
        help="Conformal threshold tau (required with -s)"
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
        help="Base output directory (default: in-tree, overwriting shipped results)"
    )
    parser.add_argument(
        "--record",
        action="store_true",
        default=False,
        help="Record calls for replay (live run; needs OPENAI_API_KEY and the record extra)"
    )
    parser.add_argument(
        "--rounds",
        action="store_true",
        default=False,
        help="Count interaction rounds"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N programs, in sorted order"
    )
    parser.add_argument(
        "--ids",
        type=str,
        default=None,
        help="JSON file with a list of program ids; only those programs are run "
             "(e.g. conformal_ids.json, the population whose model calls the shipped "
             "conformal_cache covers). Applied before --limit."
    )
    return parser.parse_args()

def log_error(err_filepath, err, stage):
    error_report = (
        f"Stage: {stage}\n"
        f"Error: {str(err)}\n"
        f"Traceback:\n{''.join(traceback.format_exception(err))}"
    )
    try:
        write_file(err_filepath, error_report)
    except Exception as e:
        print(f"Failed to log error: {e}")

def main():
    args = parse_args()
    dataset_dir = os.path.join(DATASETS_DIR, args.dataset_dir)
    kind_dir = os.path.join(dataset_dir, args.kind)

    EPIC = args.epic
    SET = args.set
    SYNC = not EPIC
    RECORD = args.record
    ROUNDS = args.rounds
    assert not (RECORD and SET), "--record and -s are mutually exclusive"

    out_dir = args.output_dir or kind_dir
    suffix = f"{VARIANT}_{'epic' if EPIC else 'py'}"
    if not SET:
        EVAL_DIRNAME = os.path.join(out_dir, "exec", f"{suffix}_replay{'_rounds' if ROUNDS else ''}")
    else:
        assert args.conformal_thresh is not None, "--conformal_thresh must be specified"
        import GQA.conformal
        GQA.conformal.init(kind_dir, args.conformal_thresh)
        EVAL_DIRNAME = os.path.join(out_dir, "conformal_exec", args.conformal_thresh)
    RECORD_DIRNAME = os.path.join(out_dir if RECORD else kind_dir, "recordings", VARIANT)
    ROUNDS_DIRNAME = os.path.join(out_dir, "rounds", suffix)

    if not SET and not RECORD and not os.path.exists(RECORD_DIRNAME):
        print(f"ERROR: Replay directory {RECORD_DIRNAME} does not exist.")
        return
    if RECORD:
        os.makedirs(RECORD_DIRNAME, exist_ok=True)
    os.makedirs(EVAL_DIRNAME, exist_ok=True)
    if ROUNDS:
        os.makedirs(ROUNDS_DIRNAME, exist_ok=True)

    if EPIC:
        filepaths = sorted(
            get_filepaths_from_dirs([os.path.join(kind_dir, "progs_epic")], extension=".prog")
        )
    elif SET:
        filepaths = sorted(
            get_filepaths_from_dirs([os.path.join(kind_dir, "progs_set")], extension=".prog")
        )
    else:
        filepaths = sorted(
            get_filepaths_from_dirs([os.path.join(kind_dir, "progs_py")], extension=".prog")
        )
    if args.ids is not None:
        with open(args.ids, "r") as f:
            ids = set(json.load(f))
        filepaths = [
            p for p in filepaths
            if os.path.splitext(os.path.basename(p))[0] in ids
        ]
    if args.limit is not None:
        filepaths = filepaths[:args.limit]

    items_meta, items = parse_items_path(dataset_dir)
    split = items_meta["split"]
    print(f"Detected items file for split '{split}' with {items_meta['num_samples']} samples and seed {items_meta['seed']}.")

    print("Loading GQA dataset...")
    image_mappings = load_gqa_images(split)

    print(f"Starting program execution for {len(filepaths)} examples...\n")
    if SET:
        from epic import imgpatch_conformal
        models = imgpatch_conformal
    elif RECORD:
        from epic import imgpatch_4o_all
        models = imgpatch_4o_all
    else:
        models = imgpatch_replay
    CONTEXT = run_utils.make_context(
        models,
        recording=RECORD,
        sync=SYNC,
        track_rounds=ROUNDS,
    )
    for fn_path in tqdm(filepaths, desc="Executing"):
        filename = os.path.basename(fn_path)
        print(f"\nProcessing: {fn_path}")
        filename_no_ext = os.path.splitext(filename)[0]

        problem_id = filename_no_ext
        image_id = items[problem_id]["imageId"]
        image = image_mappings.get(image_id)
        image = imgpatch.WrappedImage(image, image_id, CONTEXT)

        exec_filepath = os.path.join(EVAL_DIRNAME, f"{filename_no_ext}.json")
        err_filepath = os.path.join(EVAL_DIRNAME, f"{filename_no_ext}.err")
        if os.path.exists(exec_filepath) or os.path.exists(err_filepath):
            print(f"\tSkipping {filename} (already processed)")
            continue

        model_outputs_filepath = os.path.join(RECORD_DIRNAME, f"{filename_no_ext}.json")
        if ROUNDS:
            rounds_filepath = os.path.join(ROUNDS_DIRNAME, f"{filename_no_ext}.json")

        def clear_existing():
            traceback.print_exc()
            if RECORD:
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
                    with open(os.path.join(os.path.dirname(fn_path), f"{filename_no_ext}.varnames"), "r") as f:
                        varnames = eval(f.read())
                        typeguard.check_type(varnames, epics_syntax.VarNames)
                except FileNotFoundError as e:
                    log_error(err_filepath, e, "typeguard.check_type")
                    print("\tNo varnames found for EPIC. Debugging may be harder.")
                    varnames = None

                try:
                    epic_final = epics_vipergpt.finalize(epics_expr, [image], epics_vipergpt.make_mappings(CONTEXT.METHODS), varnames)
                except (NotImplementedError, Exception) as e:
                    log_error(err_filepath, e, "epics_vipergpt.finalize")
                    print("\tIgnoring due to translation failure.")
                    clear_existing()
                    continue
            else:
                program = read_file(fn_path)
                execute_command = run_utils.get_py_exec_command(program, filename, CONTEXT, ASYNC=not SYNC, SET=SET)
                if execute_command is None:
                    print(f"\tSkipping {filename} (no execute_command found)")
                    continue

            if RECORD:
                run_utils.reset_model_outputs(CONTEXT)
            elif not SET:
                try:
                    run_utils.load_model_outputs(model_outputs_filepath, CONTEXT)
                except FileNotFoundError:
                    print("\tSkipping due to missing recording.")
                    clear_existing()
                    continue
            if ROUNDS:
                CONTEXT.ROUNDS = []

            if EPIC:
                try:
                    start = time.perf_counter_ns()
                    epic_exec_result = tuple(semantics.reduce_graph_opportunistic(epic_final))[-1]
                    elapsed = time.perf_counter_ns() - start
                except (KeyError, AssertionError) as e:
                    log_error(err_filepath, e, "semantics.reduce_graph_opportunistic")
                    print("\tIgnoring due to eval failure.")
                    clear_existing()
                    continue

                try:
                    epic_exec_result_value = epics_syntax.observe_term_as_value(epic_exec_result)
                    if type(epic_exec_result_value) is str:
                        exec_result = epic_exec_result_value
                    elif type(epic_exec_result_value) is imgpatch.ImagePatch:
                        exec_result = imgpatch.info(epic_exec_result_value)
                    else:
                        assert False, (type(epic_exec_result_value), epic_exec_result_value)
                except Exception as e:
                    log_error(err_filepath, e, "epics_syntax.observe_term_as_value")
                    print("\tUnable to find result")
                    clear_existing()
                    continue
            else:
                start = time.perf_counter_ns()
                exec_result = execute_command(image)
                elapsed = time.perf_counter_ns() - start
        except Exception as e:
            log_error(err_filepath, e, "other execution error")
            print(f"\tExecution failed: {e}")
            clear_existing()
            continue

        print(f"Saving result: {filename}")
        if RECORD:
            write_json(model_outputs_filepath, CONTEXT.MODEL_OUTPUTS)
        else:
            write_json(exec_filepath, {
                "result": exec_result,
                "time_ns": elapsed,
            })
        if ROUNDS:
            write_json(rounds_filepath, CONTEXT.ROUNDS)

        print(f"\tExecution completed in {elapsed / 1e6:.2f} ms")
        print(f"\tExecution result: {exec_result}")
        print()

    print(f"\n✅ Finished processing {len(filepaths)} programs. Results saved to {EVAL_DIRNAME}.")

if __name__ == "__main__":
    main()
