import os
import json
import statistics

IMPR_THRESH = 0.975
RUNNING_TIME_THRESH = 0.1

NANOSECOND = 10**9

HERE = os.path.dirname(os.path.abspath(__file__))

# Which datasets make up each row / scatter series.  A dataset key is a tuple
# because AgentDojo is split across suites on disk.
GROUPS = {
    "gqa": [("gqa",)],
    "agentdojo": [
        ("agentdojo", "workspace"),
        ("agentdojo", "banking"),
        ("agentdojo", "slack"),
        ("agentdojo", "travel"),
    ],
    "bcp": [("bcp",)],
}

DISPLAY_NAME = {
    "gqa": "GQA",
    "agentdojo": "AD",
    "bcp": "BCP",
}


def dataset_paths(dataset):
    """Return (prog_suffix, dirs, get_interactions_total) for a dataset key."""
    if dataset[0] == "gqa":
        base = os.path.join(HERE, "datasets/gqa_val/gpt-5/epic_compiled")
        return (
            ".prog",
            {
                "progs": f"{base}/progs_py",
                "eval_py": f"{base}/exec/4o_all_py_replay",
                "eval_epic": f"{base}/exec/4o_all_epic_replay",
                "rounds": f"{base}/rounds/4o_all_epic",
            },
            # GQA records the calls made in each round, so the Python-side
            # interaction count is the total number of calls.
            lambda rounds: sum(len(l) for l in rounds),
        )
    elif dataset[0] == "agentdojo":
        suite = dataset[1]
        base = os.path.join(HERE, f"datasets/agentdojo/gpt-5/epic_compiled/{suite}")
        return (
            ".py",
            {
                "progs": f"{base}/progs_py",
                "eval_py": f"{base}/exec_py_replay",
                "eval_epic": f"{base}/exec_epic_replay",
                "rounds": f"{base}/rounds/epic",
            },
            lambda rounds: sum(n for n in rounds),
        )
    elif dataset[0] == "bcp":
        trial = 0
        base = os.path.join(HERE, f"datasets/bcp/epic_compiled/{trial}")
        return (
            ".py",
            {
                "progs": f"{base}/progs_py",
                "eval_py": f"{base}/exec_py_replay",
                "eval_epic": f"{base}/exec_epic_replay",
                "rounds": f"{base}/rounds/epic",
            },
            lambda rounds: sum(n for n in rounds),
        )
    raise ValueError(dataset)


def process_error(s):
    lines = s.split("\n")
    return {
        "stage": lines[0].split("Stage: ")[1],
        "error": lines[1].split("Error: ")[1],
        "traceback": "\n".join(lines[3:]),
    }


def load_result(directory, prog_id):
    """Load one program's execution record: ("succ"|"error"|"missing", ...)."""
    try:
        with open(os.path.join(directory, f"{prog_id}.json"), "r") as f:
            return ("succ", json.load(f))
    except FileNotFoundError:
        pass
    try:
        with open(os.path.join(directory, f"{prog_id}.err"), "r") as f:
            return ("error", process_error(f.read()))
    except FileNotFoundError:
        return ("missing",)


def collect_dataset(dataset):
    """Collect per-program (quasar, python) runtime and interaction-count pairs."""
    prog_suffix, dirs, get_interactions_total = dataset_paths(dataset)

    runtimes = []      # (quasar_seconds, python_seconds)
    interactions = []  # (quasar_count, python_count)
    mismatches = []    # programs where the two engines disagreed on the answer
    n_total = 0
    n_succ_py = 0
    n_succ_epic = 0
    n_missing_epic = 0
    errors_epic = {}   # stage -> [prog_id]

    for prog_fn in sorted(os.listdir(dirs["progs"])):
        if len(prog_fn.split(prog_suffix)) != 2:
            continue
        prog_id = prog_fn.split(prog_suffix)[0]
        n_total += 1

        res_py = load_result(dirs["eval_py"], prog_id)
        res_epic = load_result(dirs["eval_epic"], prog_id)
        try:
            with open(os.path.join(dirs["rounds"], f"{prog_id}.json"), "r") as f:
                rounds = json.load(f)
        except FileNotFoundError:
            rounds = None

        n_succ_py += res_py[0] == "succ"
        n_succ_epic += res_epic[0] == "succ"
        n_missing_epic += res_epic[0] == "missing"
        if res_epic[0] == "error":
            errors_epic.setdefault(res_epic[1]["stage"], []).append(prog_id)

        if res_epic[0] == "succ":
            assert res_py[0] == "succ"
            if res_py[1]["result"] != res_epic[1]["result"]:
                mismatches.append((prog_id, res_py[1]["result"], res_epic[1]["result"]))
            runtimes.append((
                res_epic[1]["time_ns"] / NANOSECOND,
                res_py[1]["time_ns"] / NANOSECOND,
            ))
        if rounds is not None:
            interactions.append((len(rounds), get_interactions_total(rounds)))

    return {
        "runtimes": runtimes,
        "interactions": interactions,
        "mismatches": mismatches,
        "errors_epic": errors_epic,
        "n_total": n_total,
        "n_succ_py": n_succ_py,
        "n_succ_epic": n_succ_epic,
        "n_missing_epic": n_missing_epic,
    }


def collect_group(group):
    """Collect and merge every dataset making up a group ("gqa", "agentdojo", ...)."""
    merged = {
        "runtimes": [], "interactions": [], "mismatches": [], "errors_epic": {},
        "n_total": 0, "n_succ_py": 0, "n_succ_epic": 0, "n_missing_epic": 0,
    }
    for dataset in GROUPS[group]:
        d = collect_dataset(dataset)
        for key in ("runtimes", "interactions", "mismatches"):
            merged[key] += d[key]
        for stage, progs in d["errors_epic"].items():
            merged["errors_epic"].setdefault(stage, []).extend(progs)
        for key in ("n_total", "n_succ_py", "n_succ_epic", "n_missing_epic"):
            merged[key] += d[key]
    return merged


def summarize(values, impr_thresh, min_denominator):
    """Summarize (quasar, python) pairs as fractional improvements.

    ``overall_*`` averages over pairs whose Python-side cost exceeds
    ``min_denominator``; ``impr_*`` averages over the pairs that actually
    improved, i.e. quasar < python * impr_thresh.
    """
    values_overall = [(a, b) for a, b in values if b > min_denominator]
    values_impr = [(a, b) for a, b in values if a < b * impr_thresh]
    fracs = [1 - a / b for a, b in values_overall]
    fracs_impr = [1 - a / b for a, b in values_impr if b > 0]
    return {
        "overall_mean": statistics.mean(fracs),
        "overall_stdev": statistics.stdev(fracs),
        "frac_improvable": len(values_impr) / len(values),
        "impr_mean": statistics.mean(fracs_impr),
        "impr_stdev": statistics.stdev(fracs_impr),
        "values_improvable": values_impr,
        # The same population ``overall_mean`` averages, but as per-program
        # ratios rather than fractions -- python / quasar, so 2.0 means Quasar
        # was twice as fast and 0.5 means it took twice as long.  For consumers
        # that want the distribution rather than its first two moments; the
        # figures plot these on a log axis, where the two directions are
        # symmetric.  Quasar-side zeros would make this infinite, and none occur
        # in any recorded run (a program that takes no time or no interactions
        # at all), so it is left to raise rather than guarded.
        "ratios_overall": [b / a for a, b in values_overall],
        "n": len(values),
    }


def summarize_runtimes(values):
    return summarize(values, IMPR_THRESH, RUNNING_TIME_THRESH)


def summarize_interactions(values):
    # Interaction counts are exact integers, so there is no noise floor.
    return summarize(values, 1.0, 0)
