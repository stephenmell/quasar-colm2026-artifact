#!/usr/bin/env bash
#
# Regenerate every figure and table in the paper.
#
# Usage:
#     ./gen_figs_all.sh OUTDIR
#
# Writes into OUTDIR (created if needed):
#     speedup.pdf            Quasar vs Python runtime, log-log
#     round_improvement.pdf  interaction counts, one heatmap with each cell
#                            split into a GQA and an AgentDojo triangle
#     speedup_hist.pdf       distribution of the per-program speedup factor
#                            (python / quasar, log axis), one series per
#                            benchmark
#     round_improvement_hist.pdf  the same, for interaction counts.  Each of
#                            these two is a standalone figure with its own y
#                            axis and legend, but both share one y scale
#     conformal.pdf          test error beside uncertain-prediction rate,
#                            one box per dataset in each panel
#     eval_generation.tex    tab:eval:generation, a bare tabular to \input into
#                            the paper's own float, with its numbers inline
#                            rather than as macros
#     macros.tex             \newcommand per number the paper cites, to \input
#                            in the preamble
#
# The statistics each stage prints go to stdout; only the artifacts above are
# written to OUTDIR.  Existing files of those names are overwritten.

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "usage: $(basename "$0") OUTDIR" >&2
    exit 2
fi

case "$1" in
    -h|--help)
        awk 'NR == 1 { next }
             /^#/   { sub(/^# ?/, ""); print; next }
             { exit }' "$0" >&2
        exit 0
        ;;
esac

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$1"
OUTDIR="$(cd "$1" && pwd)"

cd "$HERE"

echo "### opportunistic figures -> $OUTDIR"
uv run python gen_figs_opportunistic.py -o "$OUTDIR"

echo
echo "### conformal figures -> $OUTDIR"
uv run python gen_figs_conformal.py -o "$OUTDIR"

echo
# The Nano rows are not generated and so are passed explicitly.
echo "### generation table -> $OUTDIR/eval_generation.tex"
uv run python gen_table_generation.py --nano-base 92 65 --nano-sft 99 71 \
    -o "$OUTDIR/eval_generation.tex"

echo
echo "### macros -> $OUTDIR/macros.tex"
uv run python gen_macros.py -o "$OUTDIR/macros.tex"

echo
echo "### done"
