"""Regenerate the code-generation table (tab:eval:generation) for the paper.

Usage:
    uv run python gen_table_generation.py             # tabular to stdout
    uv run python gen_table_generation.py -o out.tex  # also write it to a file
    uv run python gen_table_generation.py --dump      # counts behind each cell

The table compares three ways of getting an LLM to emit a code action:

    Python      unrestricted Python, no subset constraint
    Ours        Python restricted to the transpilable subset by prompting,
                one generation attempt
    Multi-turn  same, but transpiler errors are fed back and the model retries

A task counts as *executed* when the model produced a program that satisfies
the approach's constraints and that program then ran without a runtime error.
For the two restricted rows the constraints are that the accepted program came
from an allowed attempt and that it transpiles; for the unrestricted Python
baseline there is no subset requirement, so only the run has to succeed.  A
task counts as *correct* when it also produced the right answer -- a substring
match against the GQA ground truth, and AgentDojo's own `utility` predicate.

Both are fractions of every task, so a subset violation counts against
Execution, as the caption says it should.

Recovering the single-attempt ("Ours") rows needs the retry artifacts the
generation pipelines leave behind, since only the final program is executed:

    AgentDojo   `progs_py/<task>.json` records one `gen_time_s` entry per
                attempt.  (Upstream also keeps each rejected program as
                `<task>.py.<n>`, and the two signals agree exactly on all four
                suites; those programs are an input to nothing here, so they
                are not shipped.)
    GQA         `progs_py/<id>.err.<n>` holds the transpiler error from
                attempt n, so a retried task has an `<id>.err.0`.

GQA retries are undercounted, so its "Ours" row is an upper bound
-----------------------------------------------------------------
GQA has no per-task record of how many attempts a program took, so retries are
inferred from the `<id>.err.<n>` files the GQA generation pipeline leaves
behind.  That inference is incomplete: of the generator's three failure
branches, `IllegalMutationException` and the catch-all `Exception` both write
an error file, but `NotImplementedError` writes nothing and simply loops.  And
`NotImplementedError` is precisely the subset violation -- epic/translator.py
raises it for every unsupported Python construct -- so the failure mode this
row exists to measure is the one that leaves no trace.

Task 10178615 proves the gap is real: it has an `.err.1` but no `.err.0`, so
its first attempt failed invisibly.  Tasks whose attempt 0 failed that way and
whose attempt 1 then succeeded leave nothing at all, and are silently counted
here as first-attempt successes.

How many is unknowable from the committed data.  For the branch that does log,
12 tasks recovered at attempt 1 and 3 failed again; applying that same 4:1
recovery ratio to the single observed unlogged failure suggests a handful of
missed tasks, so the GQA "Ours" cells are probably overstated by a few tenths
of a point.  The AgentDojo column is unaffected -- `gen_time_s` records every
attempt there regardless of why it failed.

Inputs
------
Relative to datasets/, for each generation kind (`python` and `epic_compiled`):

    gqa_val/gpt-5/<split>.json                 task list and ground truth
    gqa_val/gpt-5/<kind>/progs_py/             including the `<id>.err.0` markers
    gqa_val/gpt-5/<kind>/exec/<see GQA_EXEC>/
    gqa_val/gpt-5/epic_compiled/progs_epic/    restricted kind only
    agentdojo/gpt-5/<kind>/<suite>/progs_py/   including the `<task>.json` metadata
    agentdojo/gpt-5/<kind>/<suite>/exec_py/
    agentdojo/gpt-5/epic_compiled/<suite>/progs_epic/

The two "including" notes are load-bearing, and are the easy things to leave
behind when copying this to another checkout: without the `.err.0` markers the
single-attempt row silently duplicates the multi-turn one, and without the
`<task>.json` metadata a whole suite silently drops out of the denominator.
Both are guarded -- the first by a warning, the second by check_recorded --
but they are guards against a mistake that is otherwise invisible.

Only the *identifiers* in progs_epic and only `len(gen_time_s)` from each
progs_py/<task>.json are ever read, so a size-constrained copy of this data
could replace both with a small manifest.

The Nano rows are transcribed, not measured
-------------------------------------------
Nano Base and Nano SFT cannot be regenerated at all, so --nano-base and
--nano-sft take their two percentages as literals and the table carries a
LaTeX comment saying so.  Without them the cells render as `?` rather than
silently disappearing.  The paper reports 92/65 and 99/71.
"""

import argparse
import glob
import json
import os
import sys
from collections import namedtuple

HERE = os.path.dirname(os.path.abspath(__file__))

GQA_DIR = os.path.join(HERE, "datasets/gqa_val/gpt-5")
AGENTDOJO_DIR = os.path.join(HERE, "datasets/agentdojo/gpt-5")

SUITES = ("workspace", "travel", "slack", "banking")

# The generation kind whose programs have to stay inside the Quasar subset.
# The other kind ("python") is the unrestricted baseline.
RESTRICTED = "epic_compiled"

GQA_EXEC = {"python": "4o_all_py", RESTRICTED: "4o_all_py_replay"}
AGENTDOJO_EXEC = "exec_py"

Counts = namedtuple("Counts", "total executed correct retried")

Row = namedtuple("Row", "label kind single_attempt")

# Grouped the way the paper rules the table off.
ROW_GROUPS = [
    [
        Row("Python", "python", False),
        Row("Ours", RESTRICTED, True),
    ],
    [
        Row("Multi-turn", RESTRICTED, False),
    ],
]

# One row's measurements, so rendering and --dump share a single pass.
Measured = namedtuple("Measured", "row gqa ad_suites")


def totals(counts):
    return Counts(*(sum(field) for field in zip(*counts)))


def transpiled(progs_epic_dir):
    """Task ids whose Python program made it through the transpiler."""
    return {f[: -len(".prog")]
            for f in os.listdir(progs_epic_dir) if f.endswith(".prog")}


def check_recorded(exec_dir, tasks):
    """Every recorded execution must belong to a task we know about.

    The task list is what the percentages are divided by, so a truncated one
    does not fail loudly -- it just shrinks the denominator.  This catches the
    case where a copy of the data omitted part of a progs_py directory.
    """
    unknown = {os.path.splitext(f)[0] for f in os.listdir(exec_dir)} - set(tasks)
    if unknown:
        raise RuntimeError(
            f"{len(unknown)} execution(s) in {exec_dir} have no corresponding "
            f"task, e.g. {sorted(unknown)[:3]}; the progs_py directory beside "
            "it is probably incomplete")


# ---------------------------------------------------------------------------
# GQA
# ---------------------------------------------------------------------------

def gqa_counts(row):
    found = sorted(glob.glob(os.path.join(GQA_DIR, "*.json")))
    if len(found) != 1:
        raise RuntimeError(
            f"expected exactly one items file in {GQA_DIR}, found {found}")
    with open(found[0]) as f:
        items = json.load(f)

    base = os.path.join(GQA_DIR, row.kind)
    exec_dir = os.path.join(base, "exec", GQA_EXEC[row.kind])
    # Any `.err.<n>` at all means the first attempt failed: the generator only
    # reaches attempt n after every earlier one has.  Keying on `.err.0` alone
    # would miss 10178615, whose attempt 0 failed down the one path that
    # records nothing -- see "GQA retries are undercounted" above.
    retried = {f.partition(".err.")[0]
               for f in os.listdir(os.path.join(base, "progs_py"))
               if ".err." in f}
    in_subset = (transpiled(os.path.join(base, "progs_epic"))
                 if row.kind == RESTRICTED else None)
    check_recorded(exec_dir, items)

    executed = correct = 0
    for problem_id, item in items.items():
        if row.single_attempt and problem_id in retried:
            continue
        if in_subset is not None and problem_id not in in_subset:
            continue
        result_path = os.path.join(exec_dir, f"{problem_id}.json")
        if not os.path.exists(result_path):
            continue
        executed += 1
        with open(result_path) as f:
            answer = f"{json.load(f)['result']}"
        if item["answer"].strip().lower() in answer.strip().lower():
            correct += 1
    return Counts(len(items), executed, correct, len(retried))


# ---------------------------------------------------------------------------
# AgentDojo
# ---------------------------------------------------------------------------

def agentdojo_suite_counts(row, suite):
    base = os.path.join(AGENTDOJO_DIR, row.kind, suite)
    progs_dir = os.path.join(base, "progs_py")
    exec_dir = os.path.join(base, AGENTDOJO_EXEC)
    tasks = sorted(f[: -len(".json")]
                   for f in os.listdir(progs_dir) if f.endswith(".json"))
    in_subset = (transpiled(os.path.join(base, "progs_epic"))
                 if row.kind == RESTRICTED else None)
    check_recorded(exec_dir, tasks)

    executed = correct = retried = 0
    for task in tasks:
        with open(os.path.join(progs_dir, f"{task}.json")) as f:
            attempts = len(json.load(f)["gen_time_s"])
        retried += attempts > 1
        if row.single_attempt and attempts > 1:
            continue
        if in_subset is not None and task not in in_subset:
            continue
        result_path = os.path.join(exec_dir, f"{task}.json")
        if not os.path.exists(result_path):
            continue
        executed += 1
        with open(result_path) as f:
            if json.load(f)["utility"] is True:
                correct += 1
    return Counts(len(tasks), executed, correct, retried)


def measure(row):
    gqa = gqa_counts(row)
    ad_suites = {suite: agentdojo_suite_counts(row, suite) for suite in SUITES}
    if row.single_attempt:
        # No retries anywhere means the retry markers are missing rather than
        # that the model never needed a second turn -- and the row would then
        # silently duplicate the unrestricted-attempt one.
        for name, counts in (("GQA", gqa),
                             ("AgentDojo", totals(ad_suites.values()))):
            if not counts.retried:
                print(f"warning: no {name} task records a retry, so the "
                      f"{row.label} row will duplicate the multi-turn one; "
                      "the retry markers in progs_py are probably missing",
                      file=sys.stderr)
    return Measured(row, gqa, ad_suites)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def pct(part, whole):
    return f"{part / whole * 100:.1f}"


def render_row(measured):
    gqa = measured.gqa
    ad = totals(measured.ad_suites.values())
    cells = [
        pct(gqa.executed, gqa.total),
        pct(ad.executed, ad.total),
        pct(gqa.correct, gqa.total),
        pct(ad.correct, ad.total),
    ]
    return f"{measured.row.label} & " + " & ".join(cells) + r" \\"


def nano_group(nano_base, nano_sft):
    """The two rows that are transcribed rather than measured.

    Values arrive as strings so the caller's precision survives: the submitted
    table printed these to the integer, since the held-out split is 100 tasks.
    """
    rows = (("Nano Base", nano_base), ("Nano SFT", nano_sft))
    supplied = [label for label, values in rows if values]
    if supplied:
        lines = ["% " + " and ".join(supplied) + " transcribed from the "
                 "command line, not regenerated:",
                 "% no results for these models exist in this repo."]
    else:
        lines = ["% Nano rows have no data in this repo and no",
                 "% --nano-base/--nano-sft was given."]
    for label, values in rows:
        executed, correct = values if values else ("?", "?")
        lines.append(f"{label} & {executed} & " + r"\multicolumn{1}{c}{--} & "
                     + f"{correct} & " + r"\multicolumn{1}{c}{--} \\")
    return lines


def render_table(measured_groups, nano_rows):
    groups = [[render_row(m) for m in group] for group in measured_groups]
    groups.append(nano_rows)
    body = "\n\\midrule\n".join("\n".join(g) for g in groups)
    return "\n".join([
        # Five columns, not the submitted table's seven: it declared
        # `lrrrrrr` and filled only five, leaving two dead columns' worth of
        # \tabcolsep padding at the right edge.
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"\textbf{Approach} & \multicolumn{2}{c}{\textbf{Execution}} "
        r"& \multicolumn{2}{c}{\textbf{Accuracy}} \\",
        r"\cmidrule{2-3}\cmidrule{4-5} & \textbf{GQA} & \textbf{AD} "
        r"& \textbf{GQA} & \textbf{AD} \\",
        r"\midrule",
        body,
        r"\bottomrule",
        r"\end{tabular}",
    ])


def dump(measured_groups):
    def line(name, c):
        print(f"%   {name:13} {c.executed}/{c.total} executed, "
              f"{c.correct}/{c.total} correct, {c.retried} needed a retry")

    for group in measured_groups:
        for m in group:
            print(f"% {m.row.label}")
            line("gqa", m.gqa)
            for suite, counts in m.ad_suites.items():
                line("ad " + suite, counts)
            line("ad pooled", totals(m.ad_suites.values()))


def percentage(text):
    """Validate a literal percentage, returning it unchanged."""
    if not 0 <= float(text) <= 100:
        raise argparse.ArgumentTypeError(f"{text} is not a percentage")
    return text


def main():
    ap = argparse.ArgumentParser(
        description="Regenerate tab:eval:generation for the paper.")
    ap.add_argument("-o", "--output",
                    help="write the LaTeX tabular here as well")
    ap.add_argument("--dump", action="store_true",
                    help="also print the counts behind every cell")
    for flag, label, submitted in (("--nano-base", "Nano Base", "92 65"),
                                   ("--nano-sft", "Nano SFT", "99 71")):
        ap.add_argument(flag, nargs=2, type=percentage,
                        metavar=("EXEC", "ACC"),
                        help=f"Execution and Accuracy for the {label} row, "
                             "which has no data in this repo; the submitted "
                             f"table used {submitted}")
    args = ap.parse_args()

    measured_groups = [[measure(row) for row in group] for group in ROW_GROUPS]
    if args.dump:
        dump(measured_groups)
    table = render_table(measured_groups,
                         nano_group(args.nano_base, args.nano_sft))
    print(table)
    if args.output:
        with open(args.output, "w") as f:
            f.write(table + "\n")


if __name__ == "__main__":
    main()
