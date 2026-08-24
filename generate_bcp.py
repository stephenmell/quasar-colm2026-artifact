"""Generate BCP Python programs, via LLM (component 5).

Derived from upstream BCP/gen_prog_all.py.  Reads datasets/bcp/indices.json
and in parallel runs `BCP/gen_prog.py -t TRIAL -k KIND -i PROBLEM_ID`, which
prompts gpt-5 (reasoning effort high) and checker-regenerates until the
program passes translation.  Nondeterministic; regenerated programs will not
match the committed progs_py.  Needs OPENAI_API_KEY and
datasets/bcp/problems.jsonl (see extract_bcp_problems.py).

Usage:
  uv run python generate_bcp.py -t 0 -k epic_compiled [-w WORKERS]
"""
import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))


def load_indices(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"indices file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"indices file must contain a JSON array of strings: {path}")
    # filter to strings
    ids = [str(x) for x in data]
    return ids


def run_one(python_cmd: str, trial: str, kind : str, problem_id: str, cwd: Path = None, output_dir: str = None):
    # Build the command as requested by the user
    cmd = [python_cmd, "-m", "BCP.gen_prog", "-t", str(trial), "-k", kind, "-i", str(problem_id)] + (["-o", output_dir] if output_dir else [])
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        return {
            "problem_id": problem_id,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except Exception as e:
        return {"problem_id": problem_id, "returncode": 1, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Run BCP/gen_prog.py for each problem id in datasets/bcp/indices.json in parallel.")
    parser.add_argument("-t", "--trial", required=True, help="trial id (passed to -t)")
    parser.add_argument("-k", "--kind", required=True)
    parser.add_argument("-w", "--workers", type=int, default=os.cpu_count() or 4, help="number of parallel workers (default: cpu count)")
    parser.add_argument("--python", default="python", help="python executable to use (default: 'python')")
    parser.add_argument("--indices", default=os.path.join(HERE, "datasets", "bcp", "indices.json"), help="path to indices.json")
    parser.add_argument("--chdir", default=None, help="optional working directory to run commands in (default: repository root)")
    parser.add_argument("--fail-fast", action="store_true", help="stop submitting new jobs on first failure")
    parser.add_argument("-o", "--output_dir", default=None, help="Base datasets directory to write into (default: the in-tree datasets/)")
    args = parser.parse_args()

    indices_path = Path(args.indices)
    try:
        ids = load_indices(indices_path)
    except Exception as e:
        print(f"Error loading indices: {e}", file=sys.stderr)
        sys.exit(2)

    if not ids:
        print("No problem ids found in indices file.")
        return

    cwd = Path(args.chdir) if args.chdir else Path(HERE)

    print(f"Running {len(ids)} tasks with {args.workers} workers using python='{args.python}'")

    results = []
    failed_any = False

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as exc:
        # submit all futures, but optionally stop submitting on first failure when fail-fast is used
        future_to_id = {}
        for pid in ids:
            future = exc.submit(run_one, args.python, args.trial, args.kind, pid, cwd, args.output_dir)
            future_to_id[future] = pid

        for future in concurrent.futures.as_completed(future_to_id):
            res = future.result()
            results.append(res)
            pid = res.get("problem_id")
            rc = res.get("returncode", 1)
            if rc != 0:
                failed_any = True
                print(f"[FAIL] {pid} rc={rc}")
                # print some stderr for debugging
                if res.get("stderr"):
                    print(res.get("stderr"), file=sys.stderr)
                if args.fail_fast:
                    print("Fail-fast enabled; stopping early.")
                    break
            else:
                print(f"[OK]   {pid}")

    # Summary
    total = len(results)
    successes = sum(1 for r in results if r.get("returncode", 1) == 0)
    fails = total - successes
    print(f"Done. total={total} success={successes} failed={fails}")

    if failed_any:
        sys.exit(1)


if __name__ == "__main__":
    main()
