import os
import json
import random
import inspect
import statistics

import abstract_check


DATASETS = ("gqa", "ad")

TEST_TARGET = 0.1
N_SPLITS = 100

UNCERTAIN_SENTINEL = "__MODEL_UNCERTAIN__"

BOTTOM = "BOTTOM"

HERE = os.path.dirname(os.path.abspath(__file__))


class Config:
    def __init__(self, dataset, label, prog_suffix, dir_prefix, trial_dirs,
                 threshes, check_gt, fixed_population=False):
        self.dataset = dataset
        self.label = label
        self.prog_suffix = prog_suffix
        self.dir_prefix = dir_prefix
        self.trial_dirs = trial_dirs
        self.threshes = threshes
        self.check_gt = check_gt
        self.fixed_population = fixed_population

    @property
    def param_steps(self):
        return [(1, tau) for tau in self.threshes] + [(1, BOTTOM)]


def _config_gqa():
    dir_prefix = os.path.join(HERE, "datasets/gqa_val/gpt-5/epic_compiled")
    path_task_info = os.path.join(HERE, "datasets/gqa_val/gpt-5/val_n1000_seed2025.json")

    with open(path_task_info, "r") as f:
        task_info = json.load(f)

    def eval_match(gt: str, pred: str) -> bool:
        return gt.strip().lower() in pred.strip().lower()

    def check_gt(prog_id, pred):
        if pred == UNCERTAIN_SENTINEL:
            return True
        return eval_match(task_info[prog_id]["answer"], pred)

    return Config(
        dataset="gqa",
        label="GQA",
        prog_suffix=".prog",
        dir_prefix=dir_prefix,
        trial_dirs=("",),
        threshes=[1.0, 0.5, 0.25, 0.125],
        check_gt=check_gt,
    )


def _config_ad():
    # Imported lazily so that the GQA path does not require agentdojo.
    from agentdojo.task_suite.load_suites import get_suite

    suites_names = ("workspace", "travel")
    dir_prefix = os.path.join(HERE, "datasets/agentdojo/gpt-5/epic_compiled/")
    suites = {suite: get_suite("v1.2.1", suite) for suite in suites_names}

    def classify_utility(suite_name, tid, user_task):
        source = inspect.getsource(user_task.utility)
        n_not_strict = len(source.split("not strict")) - 1
        n_model_output_uses = len(source.split("model_output")) - 1
        n_util_calls = len(source.split(".utility(")) - 1

        assert n_model_output_uses > 0, source

        if n_util_calls == 0:
            if n_model_output_uses == 1:
                assert n_not_strict == 0, source
                return "EFFECT"
            elif n_model_output_uses > 1:
                return "PURE"
            else:
                assert False, (n_not_strict, source)
        elif n_util_calls == 2:
            assert "user_task_1.utility(" in source, source
            assert "user_task_2.utility(" in source, source
            return "TASK1 + TASK2"
        else:
            assert False, (n_util_calls, source)

    def check_gt(prog_id, pred):
        suite_name = prog_id.split("_")[0]
        tid = prog_id.replace(f"{suite_name}_", "")
        user_task = suites[suite_name].user_tasks[tid]

        if classify_utility(suite_name, tid, user_task) != "PURE":
            return None

        try:
            util = user_task.utility(
                model_output=pred,
                pre_environment=None,
                post_environment=None,
            )
            return True if pred == UNCERTAIN_SENTINEL else util
        except AttributeError:
            return None

    trial_dirs = tuple(suites_names)

    threshes = [0.5, 0.05, 0.03, 0.015, 0.0075]
    return Config(
        dataset="ad",
        label="AD",
        prog_suffix=".py",
        dir_prefix=dir_prefix,
        trial_dirs=trial_dirs,
        threshes=threshes,
        check_gt=check_gt,
        fixed_population=True,
    )


def get_config(dataset):
    if dataset == "gqa":
        return _config_gqa()
    elif dataset == "ad":
        return _config_ad()
    raise ValueError(dataset)


def load_conformal_info(cfg, verbose=False):
    """ProblemID -> (trial, tau) -> (covers, predictions)."""
    conformal_info = {}

    for trial in cfg.trial_dirs:
        trial_id = int(trial.split("_")[1]) if len(trial.split("_")) == 2 else None
        trial_num = 0 if trial_id is None else trial_id + 1

        for prog_fn in os.listdir(f"{cfg.dir_prefix}/{trial}/progs_py"):
            if len(prog_fn.split(cfg.prog_suffix)) != 2:
                continue
            prog_id = prog_fn.split(cfg.prog_suffix)[0]

            if verbose:
                print(f"Processing {prog_id}...")

            for tau in cfg.threshes:
                res_path = f"{cfg.dir_prefix}/{trial}/conformal_exec/{tau}/{prog_id}.json"
                try:
                    with open(res_path, "r") as f:
                        res = json.load(f)
                except FileNotFoundError:
                    continue

                if isinstance(res["result"], dict):
                    preds = frozenset(res["result"]["_possibilities"])
                else:
                    preds = frozenset([res["result"]])

                covers = False
                for pred in preds:
                    if pred is not None:
                        c = cfg.check_gt(prog_id, pred)
                        if c is None:
                            assert covers is not True
                            covers = None
                        elif c is True:
                            assert covers is not None
                            covers = True

                if verbose:
                    print("\t", tau, covers, len(preds), preds)
                conformal_info.setdefault(prog_id, {})[trial_num, tau] = (covers, preds)

    bottom_preds = frozenset([UNCERTAIN_SENTINEL])
    for prog_id, cells in conformal_info.items():
        cells[0, BOTTOM] = (cfg.check_gt(prog_id, UNCERTAIN_SENTINEL), bottom_preds)

    if cfg.fixed_population:
        keep = sorted(
            prog_id for prog_id, cells in conformal_info.items()
            if all((0, tau) in cells and cells[(0, tau)][0] is not None
                   for tau in cfg.threshes)
        )
        if verbose:
            print(f"population: {len(keep)} of {len(conformal_info)} tasks "
                  f"scoreable at every tau")
        conformal_info = {prog_id: conformal_info[prog_id] for prog_id in keep}

    return conformal_info


def err_for_subset(conformal_info, cfg, subset_ids, k, tau, verbose=False):
    """Error rate and uncertain-prediction rate over the union of trials 0..k-1."""
    tot_corr = 0
    tot_pure = 0
    set_sizes = []
    for task_id in subset_ids:
        task_corr = False
        task_impure = False
        task_preds = set()
        task_seen = False
        for i in range(k):
            key = i, tau
            if key in conformal_info[task_id]:
                task_seen = True
                (x, preds) = conformal_info[task_id][key]
                if x is None:
                    assert not task_corr
                    task_impure = True
                else:
                    task_preds.update(preds)
                if x is True:
                    assert not task_impure
                    task_corr = True
        if not task_seen:
            if verbose:
                print("WARNING:", tau, conformal_info[task_id])
            continue
        if task_corr:
            tot_corr += 1
        if not task_impure:
            tot_pure += 1
            # A set can also reach us flattened into the result string: .format()
            # and f-strings route through __str__, which AbstractOther does not
            # override, so its repr leaks in. Recover the size and credit it.
            is_uncertain = (
                len(task_preds) > 1
                or UNCERTAIN_SENTINEL in task_preds
                or any(abstract_check.is_uncertain(p) for p in task_preds)
            )
            set_sizes.append(is_uncertain)

    if tot_pure == 0:  # every task in the subset was skipped as missing
        return 1.0, 0.0
    return 1 - tot_corr / tot_pure, sum(set_sizes) / len(set_sizes)


def do_procedure(conformal_info, cfg, test_target, i, verbose=False):
    """One split-conformal trial: calibrate on half the tasks, measure on the rest."""
    data_ordered = sorted(conformal_info.keys())
    random.seed(i)
    random.shuffle(data_ordered)
    n = len(data_ordered) // 2
    val = data_ordered[:n]
    test = data_ordered[n:]

    val_target = test_target * n / (n + 1)

    step = None
    for (k, tau) in cfg.param_steps:
        val_err, val_unk = err_for_subset(conformal_info, cfg, val, k, tau, verbose)
        if verbose:
            print(i, k, tau, val_err, val_unk)
        if val_err < val_target:
            step = k, tau
            break

    # BOTTOM has error 0 on any subset, so some rung always passes.
    assert step is not None, "ladder fell through despite the BOTTOM rung"
    k, tau = step
    return err_for_subset(conformal_info, cfg, test, k, tau, verbose)


def compute(dataset, test_target=TEST_TARGET, n_splits=N_SPLITS, verbose=False):
    """Run the calibration procedure over n_splits random val/test splits.

    Returns a dict with the per-split distributions and their (mean, stdev),
    as fractions.
    """
    cfg = get_config(dataset)
    conformal_info = load_conformal_info(cfg, verbose=verbose)
    err_dist, unk_dist = zip(*(
        do_procedure(conformal_info, cfg, test_target, i, verbose=verbose)
        for i in range(n_splits)
    ))
    return {
        "label": cfg.label,
        "test_target": test_target,
        "err_dist": err_dist,
        "unk_dist": unk_dist,
        "err": (statistics.mean(err_dist), statistics.stdev(err_dist)),
        "unk": (statistics.mean(unk_dist), statistics.stdev(unk_dist)),
    }
