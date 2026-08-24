"""Generate every number the paper cites, as LaTeX macros.

Usage:
    uv run python gen_macros.py                 # print macros to stdout
    uv run python gen_macros.py -o macros.tex   # write them to a file
    uv run python gen_macros.py --dump          # also show the raw statistics
    uv run python gen_macros.py --no-conformal  # skip the conformal analysis

Every number the paper's prose cites comes from here.  The paper \\input{}s the
result as ``plots/macros.tex`` and cites the macros from both the prose and the
overview table, so a number can no longer say one thing in a table and another
in the sentence describing it -- which is exactly what had happened to
AgentDojo's access-control and conformal numbers before this existed.

``tab:eval:generation`` is the exception: gen_table_generation.py measures it and
emits the whole tabular with its numbers inline, because nothing outside that
table cites its cells.

``gen_table_summary.py`` emits the overview table as macro *references* rather
than numbers, so it depends on the names built here.  The names are duplicated
there as literal strings rather than imported (entry points do not import each
other, see CLAUDE.md).  Renaming one side and not the other makes the paper fail
to build with an "Undefined control sequence", so the duplication needs no guard.

Two kinds of macro come out of this file, distinguished in the output by a
``[recorded]`` tag on the comment line:

  measured   computed from datasets/ via analysis_opportunistic.py and
             analysis_conformal.py -- the same functions that feed the figures.
  recorded   a constant declared below

Percentages render as "18\\% \\pm 23": the mean is a percentage and the standard
deviation is in percentage points.
"""

import os
import json
import argparse

import analysis_opportunistic as ao
import analysis_conformal as ac


# ---------------------------------------------------------------------------
# Recorded constants -- NOT computed from datasets/.  See the module docstring.
# ---------------------------------------------------------------------------

# The 80 sampled query ids, kept as the record of which subset was drawn.
BCP_INDICES = os.path.join(ao.HERE, "datasets/bcp/indices.json")

# Models.  The synthesis model is measured -- it is the `<model>` component of
# the datasets/ layout, so regenerating the data under a different model moves
# the paper with it.  The rest cannot be: nothing in a recorded execution names
# a model.  `exec/<id>.json` holds only `result`, `time_ns` and (AgentDojo)
# `utility`; `progs_py/<task>.json` holds only `gen_time_s`.  The one other
# signal is the backend variant in GQA's exec directory name (`4o_all_py`), and
# the variant -> model mapping lives in epic/class_variants.py, not ported.
MODELS = {
    # upstream BCP/api.py -- what BCP programs call at execution time
    "BcpModel": ("GPT-5-nano", "BCP execution-time model (upstream BCP/api.py)"),
    # not recorded anywhere; the API default at the time of the runs
    "ModelCodegenEffort": ("Medium", "reasoning effort for synthesis (the API default)"),
    # the SFT experiment in sec:lang:generation.  Those runs happened outside
    # this codebase and their outputs were not kept, upstream included.
    "ModelSftStudent": ("GPT-4.1-nano", "small model fine-tuned in the SFT experiment"),
}

# How a `<model>` directory name is written in prose.  A model absent from here
# raises rather than rendering its directory name, so regenerating the data
# under a new model forces someone to decide how the paper should say it.
MODEL_DISPLAY = {"gpt-5": "GPT-5"}

# Benchmarks with a `<model>` level in their path.  BCP has none (its programs
# live at datasets/bcp/epic_compiled/0/), so it cannot corroborate.
MODEL_LEVEL_BENCHMARKS = ("gqa_val", "agentdojo")

# The SFT experiment's split.  Upstream's fine-tuning driver is not ported.
SFT_TRAIN_SIZE = "900"
SFT_HELDOUT_SIZE = "100"

# tab:eval:generation is not here.  gen_table_generation.py measures it from
# datasets/ and emits the whole tabular with its numbers inline; nothing outside
# that table cites its cells, so routing them through the preamble would buy
# nothing.  The SFT split sizes above are the exception -- the prose cites those.


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------

# The paper names its two main benchmarks GQA and AD; BCP is cited in prose
# only.  The macro prefix is the paper's name for the dataset.
GROUP_PREFIX = {"gqa": "Gqa", "agentdojo": "Ad", "bcp": "Bcp"}

# analysis_conformal keys AgentDojo as "ad"; analysis_opportunistic as "agentdojo".
CONFORMAL_KEY = {"gqa": "gqa", "agentdojo": "ad"}

# Groups whose speedup and approval-reduction averages the paper reports split
# into "all programs" and "just the ones that improved".  BCP is cited as a
# single number in prose, so it gets only the overall figure.
BREAKDOWN_GROUPS = ("gqa", "agentdojo")


def synthesis_model():
    """The `<model>` component of the datasets/ layout, as prose writes it.

    Every benchmark with that level must agree: the paper says one model
    generated all the programs, and if the recorded data stops backing that up
    the sentence is wrong rather than merely imprecise.
    """
    found = {}
    for benchmark in MODEL_LEVEL_BENCHMARKS:
        path = os.path.join(ao.HERE, "datasets", benchmark)
        models = sorted(d for d in os.listdir(path)
                        if os.path.isdir(os.path.join(path, d)))
        if len(models) != 1:
            raise RuntimeError(
                f"expected exactly one model directory under {path}, found "
                f"{models}; the paper cites a single synthesis model")
        found[benchmark] = models[0]

    distinct = set(found.values())
    if len(distinct) != 1:
        raise RuntimeError(
            f"benchmarks disagree on the synthesis model: {found}; the paper "
            "says one model generated every program")

    model = distinct.pop()
    if model not in MODEL_DISPLAY:
        raise RuntimeError(
            f"no prose spelling for model directory {model!r}; add it to "
            "MODEL_DISPLAY and check how the paper should refer to it")
    return MODEL_DISPLAY[model]


def collect(conformal=True):
    """Every quantity the paper cites, plus the populations behind them."""
    groups = {}
    for group in ("gqa", "agentdojo", "bcp"):
        data = ao.collect_group(group)
        groups[group] = {
            "data": data,
            "runtime": ao.summarize_runtimes(data["runtimes"]),
            "interactions": ao.summarize_interactions(data["interactions"]),
            # BCP has no conformal layer, so it never gets one of these.
            "conformal": (ac.compute(CONFORMAL_KEY[group])
                          if conformal and group in CONFORMAL_KEY else None),
        }

    with open(BCP_INDICES, "r") as f:
        sampled = json.load(f)
    # The sampled ids and the programs on disk must be the same 80 tasks; if
    # they ever diverge, "our subset of N tasks" is citing the wrong N.
    assert len(sampled) == groups["bcp"]["data"]["n_total"], (
        len(sampled), groups["bcp"]["data"]["n_total"])

    return {"groups": groups, "n_bcp_sampled": len(sampled),
            "synthesis_model": synthesis_model()}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def pct(x, places=0):
    return f"${x * 100:0.{places}f}\\%$"


def pct_pm(mean_stdev, places=0):
    """Render a (mean, stdev) pair of fractions, or "" if unavailable."""
    if mean_stdev is None:
        return ""
    mean, stdev = mean_stdev
    return f"${mean * 100:0.{places}f}\\% \\pm {stdev * 100:0.{places}f}$"


def duration(seconds):
    """Render a duration in whichever unit keeps it a small whole number.

    Returns math-mode *content*, without the surrounding ``$``, so the paper can
    put it inside a larger expression -- ``$\\leq \\SpeedupRuntimeFloor$``.  It
    must therefore be used in math mode: \\mathrm outside it is an error.  This
    is the one exception to the convention that a macro body is self-delimiting;
    pct() and pct_pm() both carry their own ``$``.

    The paper has no siunitx, so the unit is set with \\mathrm and a thin space.
    Sub-second thresholds read better in milliseconds, but the unit follows the
    value rather than being fixed, so moving the constant cannot leave the paper
    saying something like "2000ms".
    """
    if seconds < 1:
        # %g rather than a fixed 0 places: a sub-millisecond threshold would
        # otherwise round to a rendered "0ms".
        return f"{seconds * 1000:0.4g}\\,\\mathrm{{ms}}"
    return f"{seconds:0.4g}\\,\\mathrm{{s}}"


def measured(name, body, comment):
    return (name, body, comment, True)


def recorded(name, body, comment):
    return (name, body, comment, False)


def build_groups(stats, conformal=True):
    """Return [(section title, [(name, body, comment, is_measured)])]."""
    g = stats["groups"]
    sections = []

    # -- benchmark sizes --------------------------------------------------
    sizes = [
        measured("GqaTaskCount", str(g["gqa"]["data"]["n_total"]),
                 "GQA tasks sampled for the ViperGPT evaluation"),
        measured("AdTaskCount", str(g["agentdojo"]["data"]["n_total"]),
                 "AgentDojo tasks, summed over the four suites"),
        measured("BcpSubsetSize", str(stats["n_bcp_sampled"]),
                 "sampled BCP tasks (datasets/bcp/indices.json)"),
    ]
    sections.append(("Benchmark sizes", sizes))

    # -- models -----------------------------------------------------------
    model = stats["synthesis_model"]
    sections.append(("Models", [
        measured("ModelCodegen", model,
                 "program synthesis; the <model> level of datasets/"),
        # The SFT teacher is the same synthesis model, and the paper's sentence
        # only makes sense if it stays that way, so it is one macro's value.
        measured("ModelSftTeacher", model,
                 "large model whose programs are the SFT training set"),
    ] + [
        recorded(name, body, comment) for name, (body, comment) in MODELS.items()
    ]))

    # -- autoparallelization and access control ---------------------------
    for kind, key, what in (("Speedup", "runtime", "speedup"),
                            ("Rounds", "interactions", "reduction in user approvals")):
        entries = []
        # The runtime floor is specific to the speedup analysis: interaction
        # counts are exact integers, so summarize_interactions passes 0 for the
        # same argument and nothing is excluded there.
        if key == "runtime":
            entries.append(
                measured("SpeedupRuntimeFloor", duration(ao.RUNNING_TIME_THRESH),
                         "use in math mode: programs whose Python runtime is at "
                         "most this are excluded "
                         "(analysis_opportunistic.RUNNING_TIME_THRESH)"))
        for group in ("gqa", "agentdojo", "bcp"):
            p = GROUP_PREFIX[group]
            name = ao.DISPLAY_NAME[group]
            s = g[group][key]
            entries.append(
                measured(f"{p}{kind}Overall",
                         pct_pm((s["overall_mean"], s["overall_stdev"])),
                         f"{name}: mean {what} over all scored programs"))
            # Only the two benchmarks in the overview table break the average
            # down by improvable subset; BCP is cited in prose as a single
            # figure, and emitting the breakdown anyway left three macros
            # defined and never used.
            if group not in BREAKDOWN_GROUPS:
                continue
            entries += [
                measured(f"{p}{kind}FracImprovable", pct(s["frac_improvable"]),
                         f"{name}: share of programs that improved"),
                measured(f"{p}{kind}Improvable",
                         pct_pm((s["impr_mean"], s["impr_stdev"])),
                         f"{name}: mean {what} over just those"),
            ]
        title = ("Autoparallelization" if kind == "Speedup" else "Access control")
        sections.append((title, entries))

    # -- conformal prediction ---------------------------------------------
    conf = [
        measured("ConfTargetError", pct(ac.TEST_TARGET),
                 "target error rate of the calibration procedure"),
        measured("ConfNumSplits", str(ac.N_SPLITS),
                 "independent validation/test splits"),
    ]
    for group in ("gqa", "agentdojo"):
        p = GROUP_PREFIX[group]
        name = ao.DISPLAY_NAME[group]
        cf = g[group]["conformal"]
        conf += [
            measured(f"{p}ConfError", pct_pm(cf and cf["err"], places=1),
                     f"{name}: mean test error over the splits"),
            measured(f"{p}ConfUncertain", pct_pm(cf and cf["unk"], places=1),
                     f"{name}: mean fraction of uncertain predictions"),
        ]
    sections.append(("Conformal prediction", conf))

    # -- code generation --------------------------------------------------
    # The table's own cells come from gen_table_generation.py, not from here;
    # only the split sizes the prose cites are macros.
    sections.append(("Code generation", [
        recorded("SftTrainSize", SFT_TRAIN_SIZE,
                 "programs the small model is fine-tuned on"),
        recorded("SftHeldOutSize", SFT_HELDOUT_SIZE,
                 "held-out programs the SFT rows are scored on"),
    ]))

    return sections


def render(sections):
    lines = [
        "% Generated by gen_macros.py -- do not edit by hand.",
        "%",
        "% Every number the paper's prose cites.  Macros tagged [recorded] are",
        "% constants declared in gen_macros.py rather than computed from datasets/,",
        "% because what produced them is not in this repo; the rest come from",
        "% analysis_opportunistic.py and analysis_conformal.py, the same functions",
        "% that feed the figures.",
    ]
    for title, entries in sections:
        lines += ["", f"% ==== {title} " + "=" * max(0, 60 - len(title)), ""]
        for name, body, comment, is_measured in entries:
            tag = "" if is_measured else "[recorded] "
            lines.append(f"% {tag}{comment}")
            lines.append(f"\\newcommand{{\\{name}}}{{{body}}}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", help="write the macros here as well")
    ap.add_argument("--dump", action="store_true",
                    help="also print the raw statistics as LaTeX comments")
    ap.add_argument("--no-conformal", action="store_true",
                    help="skip the conformal analysis and leave those macros empty")
    args = ap.parse_args()

    conformal = not args.no_conformal
    stats = collect(conformal=conformal)
    if args.dump:
        scalars = ("overall_mean", "overall_stdev", "frac_improvable",
                   "impr_mean", "impr_stdev", "n")
        for group, g in stats["groups"].items():
            d = g["data"]
            print(f"% {group}: n={d['n_total']} py_succ={d['n_succ_py']} "
                  f"epic_succ={d['n_succ_epic']} epic_missing={d['n_missing_epic']}")
            for stage, progs in d["errors_epic"].items():
                print(f"%   quasar error in {stage}: {', '.join(progs)}")
            for key in ("runtime", "interactions"):
                body = ", ".join(f"{k}={g[key][k]:.4g}" for k in scalars)
                print(f"%   {key + ':':14}{body}")
            if g["conformal"]:
                print(f"%   {'conformal:':14}err={g['conformal']['err']} "
                      f"unk={g['conformal']['unk']}")

    text = render(build_groups(stats, conformal=conformal))
    print(text)
    if args.output:
        with open(args.output, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
