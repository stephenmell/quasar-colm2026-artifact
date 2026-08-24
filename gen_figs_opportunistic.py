"""Generate the execution-trace figures: speedup scatter, interaction heatmaps, CDFs.

Usage:
    uv run python gen_figs_opportunistic.py               # write PDFs to /tmp
    uv run python gen_figs_opportunistic.py -o figs/      # write them elsewhere
    uv run python gen_figs_opportunistic.py --cdf         # add the CDF variants
    uv run python gen_figs_opportunistic.py --mismatches  # list result disagreements

Produces:
    speedup.pdf            Quasar vs Python runtime, log-log
    round_improvement.pdf  interaction counts for every benchmark drawn, one
                           heatmap with each cell split into a wedge per
                           benchmark -- a GQA and an AgentDojo triangle by
                           default
    speedup_hist.pdf       distribution of the per-program speedup factor
    round_improvement_hist.pdf  the same, for interaction counts

and with --cdf, the same two distributions drawn as CDFs instead:

    speedup_cdf.pdf
    round_improvement_cdf.pdf

The first two figures show the raw (python, quasar) pair per program; the rest
show the distribution of the derived ``python / quasar`` ratio, one series per
benchmark.  That ratio reads as a factor (2x, 1/2x) and is drawn on a log axis,
where being twice as fast and half as fast are the same distance from 1x.  The
histograms bin it geometrically; see plot_improvement_hist.

The paper carries the histograms, so the CDFs are off by default -- they answer
a different question (what fraction of programs beat a given factor) and are
kept for reading the distribution during analysis, not for publication.

--paired draws the two histograms as the halves of one side-by-side figure: one
y axis and one legend between them.  Without it each is a standalone figure
carrying its own axis and legend -- which is what the paper prints, side by
side; run_all.sh records why it leaves --paired off.  Either way both are drawn
to the same y limit, the larger of the two, so bar heights are comparable
between the figures however they are placed.

Note the paper's own numbers are *fractional reductions* (``1 - quasar /
python``), not these factors, and the two do not convert through their means.

The scatter and the heatmap draw every program, including the mass sitting on
the diagonal; --improved-only restricts them to the programs Quasar improved,
and --include-bcp adds a third benchmark to every figure.  The distribution
figures ignore --improved-only and always draw their whole population -- see
plot_improvement_cdf.  The statistics printed to stdout always cover every
program, whatever the figures show.
"""

import os
import math
import argparse

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb
from matplotlib.lines import Line2D
from matplotlib.path import Path

import analysis_opportunistic as ao
import figure_style


# Both sizes go through figure_style.scaled, which divides by TEXT_SCALE to make
# the type render bigger on the page; the numbers below are the unscaled shapes.
FIGSIZE = figure_style.scaled((8, 6))
# The distribution figures are shorter than the scatter and the heatmap, which
# both want square-ish axes -- a histogram does not, and these two are printed
# side by side, where 8x6 each is a lot of page.  Only the height changes, so at
# a given \includegraphics width the text still comes out the same size on the
# page as in the other figures; the figure is simply less tall.
#
# The height is *not* scaled, and must not be.  "Fraction of Programs" is
# rotated and needs 2.85in of axes height, the x label and ticks take about
# 1.1in off the figure before the axes start, and none of that shrinks with the
# figure because it is all measured in points -- so the 3.9in floor is in
# absolute inches and does not move with TEXT_SCALE.  Writing a scaled height
# here means the label silently overflows the next time TEXT_SCALE is raised,
# which is exactly what happened at 1.3.
#
# The width is taken from FIGSIZE so the two kinds of figure scale together: at
# equal \includegraphics width their type comes out the same size.
FIGSIZE_DIST = (FIGSIZE[0], 4.0)
# The speedup scatter is drawn with equal aspect, so that a decade on one axis
# is a decade on the other and the equal-execution-time line lies at 45 degrees.
#
# It shares FIGSIZE with the heatmap rather than taking a square canvas of its
# own, because the two are meant to read as the same size on the page and a
# figure's on-page scale is set by its *width*: LaTeX scales by L/W, so equal
# core sizes need equal W and equal core.  The heatmap spends its surplus width
# on two colorbars; the scatter leaves the same strip blank, which also lines the
# two plot areas up when the figures are stacked.
FIGSIZE_SQUARE = FIGSIZE

# Side of the square plotting area, in inches, for both the scatter and the
# heatmap.  This is what the heatmap's axes measures once its colorbars and
# labels have taken their share of FIGSIZE; the scatter is then pinned to it
# rather than filling its canvas.  plot_interactions re-measures on every run and
# complains if the heatmap drifts off it, since nothing else would notice.
CORE_SIZE_IN = 4.0
CORE_SIZE_TOL_IN = 0.05

# Slack at each end of the scatter's axes, as a multiplicative factor, since the
# axes are logarithmic.  Explicit limits are needed for the equal aspect to mean
# anything, and they replace the automatic margins matplotlib would have added.
AXIS_PAD = 1.25
AXIS_LABEL_FONTSIZE = 22
TICK_FONTSIZE = 15
LEGEND_FONTSIZE = 16

# The distribution figures print side by side, so each is included at about half
# the width the scatter and the heatmap get, and everything in them lands on the
# page correspondingly smaller.  Their ticks were the part that showed it, so
# they get their own size; the axis labels and legend still read at the shared
# ones.  Set relative to TICK_FONTSIZE so a change there carries over.
TICK_FONTSIZE_DIST = TICK_FONTSIZE + 3

# Interaction counts are plotted on a fixed grid of HIST_MIN..HIST_MAX.  The
# tail past HIST_MAX is *not* negligible -- Python counts reach 91, and 8% of
# GQA / 25% of AgentDojo improved programs sit beyond 14 -- so the overflow is
# clipped into the final row and column (labelled "14+") rather than dropped.
# Every grid therefore sums to 1.0.
#
# Every GQA program interacts at least once on both sides, so a 0 row and
# column would only ever be empty there.  AgentDojo has two programs that
# interact zero times under both Python and Quasar (dropped from the population
# under --improved-only, since they are not improvements); those go undrawn rather
# than being clipped up into the 1 cell, which would misreport their count.
# They stay in the denominator, so AgentDojo's grid sums to just under 1.0.
#
# HIST_MAX is one below the largest Quasar count (14), which leaves a single
# GQA program -- (python=19, quasar=14) -- clipped onto the corner cell, where
# it sits on the "equal interactions" diagonal despite having improved.  Raising
# the bound to 15 empties that corner, at the cost of two more mostly-blank
# rows; see the note in the module docstring.
HIST_MIN = 1
HIST_MAX = 14
N_CELLS = HIST_MAX - HIST_MIN + 1

# Both from figure_style, which is the single definition for every figure the
# paper carries; assigning a group's hue explicitly also keeps it fixed when
# --include-bcp changes how many series are drawn.
GROUP_COLOR = figure_style.GROUP_COLOR
ALPHA = figure_style.SERIES_ALPHA

# The benchmarks the figures cover by default, in drawing order.
INTERACTION_GROUPS = ("gqa", "agentdojo")

# BCP is collected and reported (see gen_macros_bcp.py), but it is not one of
# the benchmarks the paper's figures or overview table cover, and its runtimes
# span a wider range that stretches the scatter's axes.  --include-bcp adds it
# to both figures; nothing else needs to change to promote it permanently.
#
# Caveat for the interaction heatmap: BCP's counts are an order of magnitude
# off the other two -- Python 40..276 approvals against Quasar 2..4 -- so every
# BCP program clips into the HIST_MAX corner and the wedge carries no
# information.  Drawing BCP there usefully needs a different binning (log axes,
# or a much larger HIST_MAX), not just this flag.  The per-group clipping counts
# printed by main() make it obvious when this is happening.
OPTIONAL_GROUPS = ("bcp",)


def hide_frame(ax):
    """Drop the axes frame; the dashed grid already carries the scale."""
    for spine in ax.spines.values():
        spine.set_visible(False)


def group_cmap(group):
    """A white-to-dark sequential ramp built around the benchmark's own hue.

    The midpoint is exactly ``GROUP_COLOR[group]``, so a filled cell reads as
    the same colour the speedup scatter uses for that benchmark.
    """
    base = GROUP_COLOR[group]
    dark = tuple(0.55 * c for c in to_rgb(base))
    return LinearSegmentedColormap.from_list(f"{group}_ramp",
                                             ["#ffffff", base, dark])


def fmt_summary(group, stats):
    return (f"\t{group} & {stats['frac_improvable']:0.2f}"
            f" & {stats['overall_mean']:0.2f} \\pm {stats['overall_stdev']:0.2f}"
            f" & {stats['impr_mean']:0.2f} \\pm {stats['impr_stdev']:0.2f}")


def plot_speedup(collected, outdir, groups, only_improved=False):
    """Scatter each group in ``groups``: Quasar runtime against Python runtime.

    With ``only_improved`` the plot keeps just the programs Quasar sped up by
    more than the noise floor, which is under half of them; otherwise every
    program is drawn, including the mass sitting on the diagonal.

    Either way, programs whose Python runtime is under
    ``ao.RUNNING_TIME_THRESH`` are excluded, matching the population the
    ``overall_*`` statistics average over.  Below that floor the timings are
    dominated by fixed overhead: AgentDojo has 18 such programs, all in the
    0.3-3.4 ms range and all nominally "slower under Quasar", and drawing them
    would stretch the axes over three decades of empty space to show noise.

    Every collected group is summarized to stdout regardless of what is drawn.
    """
    fig = plt.figure(figsize=FIGSIZE_SQUARE)
    ax1 = fig.add_subplot(1, 1, 1)
    min_val = None
    max_val = None

    print("==== SPEEDUPS")
    for group, data in collected.items():
        stats = ao.summarize_runtimes(data["runtimes"])
        print(fmt_summary(group, stats))
        if group not in groups:
            continue

        pairs = stats["values_improvable"] if only_improved else data["runtimes"]
        drawn = [(a, b) for a, b in pairs if b > ao.RUNNING_TIME_THRESH]
        if len(drawn) < len(pairs):
            print(f"\t  ({len(pairs) - len(drawn)} of {len(pairs)} below the "
                  f"{ao.RUNNING_TIME_THRESH}s floor, not drawn)")
        epic_values, py_values = zip(*drawn)
        # Drawing everything is an order of magnitude more points, most of them
        # piled along the diagonal, so shrink the marker to keep it readable.
        ax1.scatter(py_values, epic_values, alpha=ALPHA, color=GROUP_COLOR[group],
                    s=12 if not only_improved else None,
                    label=ao.DISPLAY_NAME[group])

        lo = min(min(epic_values), min(py_values))
        hi = max(max(epic_values), max(py_values))
        min_val = lo if min_val is None else min(lo, min_val)
        max_val = hi if max_val is None else max(hi, max_val)

    ax1.plot([min_val, max_val], [min_val, max_val], '--', color='gray',
             label='Equal')
    ax1.plot([min_val * 2, max_val], [min_val, max_val / 2], '--', color='gray',
             label='2x')
    plt.ylabel('Quasar Execution Time (s)', fontsize=AXIS_LABEL_FONTSIZE)
    plt.xlabel('Python Execution Time (s)', fontsize=AXIS_LABEL_FONTSIZE)
    plt.xscale("log")
    plt.yscale("log")
    # Both axes over the same range, then equal aspect.  On log axes "equal"
    # means equal *decades*, which is what puts the equal-execution-time line at
    # 45 degrees; without matching limits the two axes would still cover
    # different spans and the line would come out at some other angle.  The
    # padding is multiplicative because it is applied in log space.
    ax1.set_xlim(min_val / AXIS_PAD, max_val * AXIS_PAD)
    ax1.set_ylim(min_val / AXIS_PAD, max_val * AXIS_PAD)
    ax1.set_aspect("equal")
    # Pinned, not "best": nearly every program lands on or below the diagonal, so
    # the upper left is reliably empty, whereas "best" hunts for a gap and -- once
    # the axes shrank to CORE_SIZE_IN -- started choosing one in the middle of the
    # data.  Matches where the heatmap puts its legend, too.
    #
    # Stacked in one column.  That only clears the data because the reference
    # lines are labelled "Equal" and "2x" rather than spelled out -- the long
    # labels made the legend wide enough to reach the diagonal, which is what had
    # forced two columns.
    plt.legend(fontsize=LEGEND_FONTSIZE, loc="upper left")
    plt.xticks(fontsize=TICK_FONTSIZE)
    plt.yticks(fontsize=TICK_FONTSIZE)
    plt.grid(True, linestyle='--', alpha=0.5)
    hide_frame(ax1)
    plt.tight_layout()
    # tight_layout has just sized the axes to fill what the labels left over;
    # shrink it to the heatmap's core instead, keeping the left and bottom
    # margins it worked out so the labels still clear.  The surplus is left blank
    # on the right, opposite the heatmap's colorbars.  Done after tight_layout,
    # which would otherwise undo it, and it holds under the equal aspect because
    # a square box with square limits already satisfies that.
    pos = ax1.get_position()
    fig_w, fig_h = fig.get_size_inches()
    ax1.set_position([pos.x0, pos.y0,
                      CORE_SIZE_IN / fig_w, CORE_SIZE_IN / fig_h])
    plt.savefig(os.path.join(outdir, "speedup.pdf"))
    plt.close()


def interaction_grid(collected, group, only_improved=False):
    """Fraction of ``group``'s programs falling in each (python, quasar) cell.

    Counts above ``HIST_MAX`` are clipped into the edge row/column rather than
    dropped.  Counts below ``HIST_MIN`` are left undrawn: clipping them upward
    would file a program under an interaction count it does not have, and the
    only cases are AgentDojo's two zero-interaction programs.  They stay in the
    denominator regardless, so the fractions remain fractions of the whole
    population and the grid sums to slightly under 1.0 -- undrawn is not the
    same as nonexistent.

    Cell (i, j) holds the value pair ``(HIST_MIN + i, HIST_MIN + j)``.  Returns
    the grid, the total population, how many were clipped into the edge, and how
    many fell below ``HIST_MIN`` and so went undrawn.
    """
    pairs = collected[group]["interactions"]
    if only_improved:
        # Match the scatter: show the programs Quasar improved, not the mass of
        # programs sitting on the diagonal.
        pairs = ao.summarize_interactions(pairs)["values_improvable"]
    epic_values, py_values = zip(*pairs)
    py_values = np.asarray(py_values)
    epic_values = np.asarray(epic_values)

    n_total = len(py_values)
    drawn = (py_values >= HIST_MIN) & (epic_values >= HIST_MIN)
    py_values, epic_values = py_values[drawn], epic_values[drawn]
    n_undrawn = n_total - len(py_values)

    py = np.minimum(py_values, HIST_MAX) - HIST_MIN
    epic = np.minimum(epic_values, HIST_MAX) - HIST_MIN
    n_clipped = int(((py_values > HIST_MAX) | (epic_values > HIST_MAX)).sum())

    edges = np.arange(N_CELLS + 1)
    counts, _, _ = np.histogram2d(py, epic, bins=[edges, edges])
    # Divided by the whole population, not just the drawn part.
    return counts / n_total, n_total, n_clipped, n_undrawn


def decorate_interactions(ax, diagonal_label=None):
    ax.plot([0, N_CELLS], [0, N_CELLS], '--', color='gray', label=diagonal_label)
    positions = np.arange(N_CELLS)
    # Ticks stay on every cell so the grid does, but past ~10 cells the labels
    # collide, so only every ``stride``-th one is written.  ``HIST_MAX`` is
    # always labelled: it is the overflow bucket and must not go unmarked.
    stride = 1 + (N_CELLS > 11)
    values = HIST_MIN + positions
    labels = [str(v) if (HIST_MAX - v) % stride == 0 else ""
              for v in values[:-1]] + [f"{HIST_MAX}+"]
    # Labels sit at cell centres, on the major ticks.  The grid is hung off a
    # second set of ticks at the cell edges instead, so the lines run between
    # cells rather than straight through them; those minor ticks are drawn with
    # zero length so only the labelled ones show a mark on the axis.
    edges = np.arange(N_CELLS + 1)
    ax.set_xticks(positions + 0.5)
    ax.set_xticklabels(labels, fontsize=TICK_FONTSIZE)
    ax.set_yticks(positions + 0.5)
    ax.set_yticklabels(labels, fontsize=TICK_FONTSIZE)
    ax.set_xticks(edges, minor=True)
    ax.set_yticks(edges, minor=True)
    ax.tick_params(which="minor", length=0)
    ax.set_xlim(0, N_CELLS)
    ax.set_ylim(0, N_CELLS)
    ax.grid(False, which="major")
    ax.grid(True, which="minor", linestyle='--', alpha=0.5)
    ax.set_aspect("equal")
    hide_frame(ax)


def add_colorbar(fig, mappable, ax, label="Fraction of Programs", title=None,
                 ticks=True, **kwargs):
    cbar = fig.colorbar(mappable, ax=ax, **kwargs)
    cbar.ax.tick_params(labelsize=TICK_FONTSIZE)
    # Match the axes, which carry no frame either.
    cbar.outline.set_visible(False)
    if not ticks:
        cbar.ax.set_yticklabels([])
    if label:
        cbar.set_label(label, fontsize=LEGEND_FONTSIZE)
    if title:
        cbar.ax.set_title(title, fontsize=LEGEND_FONTSIZE - 3, pad=8)
    return cbar


# Each cell is divided into one wedge per benchmark, fanning out from the cell
# centre.  The first wedge boundary sits on the anti-diagonal -- slope -1, so a
# split line is never confused with the slope +1 "equal interactions" reference
# -- which for two benchmarks makes the wedges exactly the lower and upper
# triangles the figure has always used.
CELL_CENTER = (0.5, 0.5)
FIRST_BOUNDARY_DEG = 135.0
CORNER_DEG = (45.0, 135.0, 225.0, 315.0)


def _cell_edge(deg):
    """Where a ray leaving the cell centre at ``deg`` meets the cell boundary."""
    dx, dy = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    # The unit square's boundary is where the larger of |dx|, |dy| reaches 0.5.
    t = 0.5 / max(abs(dx), abs(dy))
    return (CELL_CENTER[0] + t * dx, CELL_CENTER[1] + t * dy)


def cell_polys(n):
    """Split the unit cell into ``n`` equal-angle wedges, in drawing order.

    A wedge runs centre -> boundary point -> any cell corners it sweeps past ->
    boundary point.  At ``n == 2`` the two boundary points are the (1, 0) and
    (0, 1) corners and the centre lies on the segment between them, so the
    wedges are the anti-diagonal triangles, unchanged from before this was
    generalized.
    """
    step = 360.0 / n
    polys = []
    for k in range(n):
        start = FIRST_BOUNDARY_DEG + k * step
        swept = sorted((c for c in CORNER_DEG if 0 < (c - start) % 360 < step),
                       key=lambda c: (c - start) % 360)
        polys.append((CELL_CENTER,
                      _cell_edge(start),
                      *(_cell_edge(c) for c in swept),
                      _cell_edge(start + step)))
    return polys


def _cell_marker(poly):
    """One wedge as a legend marker, in the marker's unit box."""
    pts = [(x - 0.5, y - 0.5) for x, y in poly]
    return Path(pts + [pts[0]], closed=True)


def plot_interactions(grids, filename, outdir):
    """Every benchmark in one panel, each cell split into one wedge apiece.

    ``grids`` is keyed by benchmark, in drawing order.  Each benchmark gets its
    own hue ramp, but all ramps share one normalization, so darkness stays
    comparable across benchmarks -- hue says *which* series, lightness says
    *how much*.  Separate scales per benchmark would make wedge-vs-wedge
    darkness comparisons meaningless.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE)
    norm = Normalize(vmin=0, vmax=max(g.max() for g in grids.values()))
    groups = list(grids)
    cmaps = {group: group_cmap(group) for group in groups}
    polys = cell_polys(len(groups))

    colls = {}
    for group, poly in zip(groups, polys):
        grid = grids[group]
        verts, values = [], []
        for xi, yi in zip(*np.nonzero(grid)):
            verts.append([(xi + dx, yi + dy) for dx, dy in poly])
            values.append(grid[xi, yi])
        colls[group] = PolyCollection(verts, array=np.array(values),
                                      cmap=cmaps[group], norm=norm,
                                      edgecolors="none")
        ax.add_collection(colls[group])

    decorate_interactions(ax)
    # One bar per hue, all on the same scale, so only the outermost carries the
    # ticks and axis label.  Each new colorbar is inserted *between* the axes
    # and the previous one, so building them back-to-front leaves them in
    # drawing order from left to right.
    for i, group in enumerate(reversed(groups)):
        outermost = i == 0
        add_colorbar(fig, colls[group], ax, fraction=0.046,
                     label="Fraction of Programs" if outermost else None,
                     title=ao.DISPLAY_NAME[group], ticks=outermost)

    handles = [Line2D([], [], linestyle="none", marker=_cell_marker(poly),
                      markersize=18, markerfacecolor=cmaps[group](0.55),
                      markeredgecolor="none", label=ao.DISPLAY_NAME[group])
               for group, poly in zip(groups, polys)]
    handles.append(Line2D([], [], linestyle="--", color="gray",
                          label="Equal"))
    ax.legend(handles=handles, fontsize=LEGEND_FONTSIZE, loc="upper left")
    ax.set_xlabel("Python Interaction Count", fontsize=AXIS_LABEL_FONTSIZE)
    ax.set_ylabel("Quasar Interaction Count", fontsize=AXIS_LABEL_FONTSIZE)
    fig.tight_layout()
    # This figure's plot area is what CORE_SIZE_IN records, and the scatter is
    # pinned to that number.  It falls out of the colorbars and labels rather
    # than being set anywhere, so anything that changes them silently moves it
    # and the two figures stop matching.  Say so instead.
    fig.canvas.draw()
    core = ax.get_window_extent()
    side_in = min(core.width, core.height) / fig.dpi
    if abs(side_in - CORE_SIZE_IN) > CORE_SIZE_TOL_IN:
        print(f"  warning: heatmap plot area is {side_in:0.2f}in, not the "
              f"CORE_SIZE_IN={CORE_SIZE_IN}in the scatter is drawn to; they will "
              f"no longer match on the page")
    fig.savefig(os.path.join(outdir, filename))
    plt.close(fig)


# Both distribution figures are drawn for both quantities, so all four come from
# one table rather than from four near-identical functions.  Each entry is
# (filename stem, key into a collected group, summarizer, axis label); the stem
# matches the raw-data figure for the same quantity, suffixed _cdf / _hist.
#
# Both axes are the ratio python / quasar, so the number reads as a factor: 2x
# means Quasar was twice as fast, or asked half as many questions, and 1/2x
# means it took twice as long.
QUANTITIES = (
    ("speedup", "runtimes", ao.summarize_runtimes,
     "Execution Time Speedup Factor"),
    ("round_improvement", "interactions", ao.summarize_interactions,
     "Interaction Count Reduction Factor"),
)

# Where each histogram sits when the paper prints the two side by side, which
# --paired uses to drop the furniture the other panel already carries: the left
# panel keeps the shared y axis, the right keeps the legend.  Change this if the
# paper ever swaps them -- nothing here infers the order from the figures.
PAIRED_SIDE = {"round_improvement": "left", "speedup": "right"}

# Below this ratio Quasar was genuinely slower, rather than equal to within the
# timing noise -- ``ao.IMPR_THRESH`` read in the other direction.  It decides
# only whether a panel acknowledges the region below 1x at all, not where any
# bin falls: GQA's slowest program is 0.993x, which is noise and should not win
# the runtime figures a labelled half-octave nothing lives in.
REGRESSION_FLOOR = ao.IMPR_THRESH


def fmt_ratio(v):
    """Tick label for a ratio: 2 -> "2x", 0.5 -> "1/2x"."""
    return f"{v:g}x" if v >= 1 else f"1/{1 / v:g}x"


def configure_ratio_axis(ax, lo, hi, pad, regressions):
    """Log x-axis labelled in powers of two, spanning ``[lo, hi]`` with air.

    A tick sits at the value it names.  That serves the histograms as well as
    the CDFs: their grid is centred on the powers of two (see
    improvement_bins), so each label also lands in the middle of the bars it
    describes.

    ``lo`` and ``hi`` are the unpadded extent, padded here rather than by the
    caller.  ``regressions`` says whether the panel holds programs Quasar
    actually made slower, and is a separate argument because it cannot be
    recovered from ``lo``: the histogram's leftmost bin reaches below 1x on
    every panel, including the interaction ones whose smallest ratio is exactly
    1x, so keying off the extent would win those a labelled half-octave with
    nothing in it.

    A log axis is what makes the two directions comparable: 2x faster and 2x
    slower are the same distance from 1, which is not true of the fractional
    reduction this replaced -- there, halving the runtime scores +0.5 but
    doubling it scores -1.0, and a handful of regressions can swamp a mean that
    improvements cannot push past 1.
    """
    ax.set_xscale("log")
    # Ticks are powers of two, so a panel whose data stops just short of one
    # would carry none on that side.  That is only a problem below 1x, where the
    # few programs Quasar made slower would sit with nothing to read them
    # against: extend to the enclosing power of two so 1/2x is labelled.  Above
    # 1x the range always spans several, and extending would only add blank.
    lo = 2.0 ** math.floor(math.log2(lo)) if regressions else lo / pad
    hi = hi * pad
    ticks = 2.0 ** np.arange(math.floor(math.log2(lo)),
                             math.ceil(math.log2(hi)) + 1)
    keep = (ticks >= lo) & (ticks <= hi)
    ax.set_xticks(ticks[keep])
    ax.set_xticklabels([fmt_ratio(v) for v in ticks[keep]],
                       fontsize=TICK_FONTSIZE_DIST)
    # The default log minor ticks would put unlabelled marks between every
    # power of two, which the dashed grid then draws over the whole panel.
    ax.minorticks_off()
    ax.set_xlim(lo, hi)


def ecdf(values):
    """Step-plot coordinates for the empirical CDF of ``values``.

    Right-continuous: drawn with ``steps-post``, the curve sits at ``y[i]``
    over ``[x[i], x[i+1])``, so a repeated value -- and interaction counts
    repeat heavily, with every unimproved program landing on exactly 0 -- shows
    as one vertical jump of the right height rather than as a slope.  The
    duplicated leading point pins the curve to 0 at the smallest observation.
    """
    xs = np.sort(np.asarray(values, dtype=float))
    ys = np.arange(1, len(xs) + 1) / len(xs)
    return np.concatenate([xs[:1], xs]), np.concatenate([[0.0], ys])


def plot_improvement_cdf(collected, groups, key, summarize, xlabel, filename,
                         outdir):
    """CDF of per-program improvement factor, one curve per benchmark.

    The complement of the scatter and the heatmap: those show the raw (python,
    quasar) pair for each program, this shows the distribution of the derived
    ``python / quasar`` ratio.  Reading it: the height where a curve crosses 1x
    is the fraction of programs Quasar did *not* improve, and the horizontal
    span above that is how the rest are spread -- both of which a mean and a
    standard deviation hide.

    The population is exactly the one ``summarize`` averages over, so the curve
    and the reported mean cover the same programs -- though the paper's mean is
    of the fractional reduction, not of this ratio, and the two do not convert
    (the mean of ``1 - q/p`` is not ``1 -`` the mean of ``q/p``).  For runtimes
    the population excludes anything under ``ao.RUNNING_TIME_THRESH``, as the
    scatter does; for interaction counts it excludes only programs with no
    Python-side interactions at all, which is undefined rather than unimproved.

    ``--improved-only`` does not apply here.  Restricting a CDF to the programs
    that improved would cut it off at the very point it exists to show.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE_DIST)
    lo = hi = 1.0
    for group in groups:
        ratios = summarize(collected[group][key])["ratios_overall"]
        xs, ys = ecdf(ratios)
        lo, hi = min(lo, xs[0]), max(hi, xs[-1])
        ax.plot(xs, ys, drawstyle="steps-post", linewidth=2, alpha=ALPHA,
                color=GROUP_COLOR[group],
                label=ao.DISPLAY_NAME[group])
        print(f"  {group}: {len(ratios)} programs, median "
              f"{np.median(ratios):0.2f}x, "
              f"{np.mean(np.asarray(ratios) <= 1):0.3f} at or below 1x")

    # Not a data series, so gray dashed like the reference lines in the other
    # two figures.  Everything left of it is a program Quasar made worse -- so
    # it is drawn only when something is: interaction counts never regress, and
    # there the rule would sit on the axis and claim a legend entry for a
    # region of the plot that does not exist.
    regressions = lo < REGRESSION_FLOOR
    if regressions:
        ax.axvline(1.0, linestyle='--', color='gray', label='No Improvement')
    configure_ratio_axis(ax, lo, hi, pad=1.08, regressions=regressions)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
    ax.set_ylabel("Fraction of Programs", fontsize=AXIS_LABEL_FONTSIZE)
    ax.tick_params(labelsize=TICK_FONTSIZE_DIST)
    # Which corner is free depends on where the curves saturate, and that moved
    # when the axis became logarithmic -- GQA now reaches 1.0 by 4x and fills
    # the upper left.  Unlike the histogram there is no full-height patch to
    # confuse the placement search, so matplotlib can pick.
    ax.legend(fontsize=LEGEND_FONTSIZE, loc="best")
    ax.grid(True, linestyle='--', alpha=0.5)
    hide_frame(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, filename))
    plt.close(fig)


# Histogram binning: one uniform geometric grid, IMPR_BINS_PER_OCTAVE bins per
# doubling, so every bin is the same width on the log axis the figures use and
# every bar really is comparable to its neighbour.  Nothing about 1x is special
# to the grid -- the bucket holding it is an ordinary bin, just a narrow enough
# one that "Quasar changed nothing" does not get averaged in with a real
# improvement.  Three per octave puts that bucket at [0.891, 1.122).
#
# It is a genuine trade, not a free choice.  A coarser grid widens the bucket
# until it swallows real improvements: at two per octave it reaches 1.19x and
# takes in AgentDojo's smallest interaction improvement (8/7, at 1.14x), and a
# runtime speedup short of 1.19x reads as noise.  At three per octave the
# interaction bucket holds exactly the programs whose count did not change --
# the next-smallest ratio above 1x in either benchmark, that same 8/7, clears
# the bucket's 1.122 lip -- so a finer grid buys nothing there and stretches
# GQA's interaction figure to 23 bins, most of them empty tail past 8x.
#
# The grid is centred on the powers of two: 1x sits in the middle of its bin,
# and so do 2x, 4x and the rest.  Centring earns its keep twice over.  The
# ratios pile up on exact powers of two -- half of GQA's interaction ratios
# are exactly 1x and a fifth exactly 2x -- and centring puts that mass in the
# middle of a bin rather than on a boundary: the edges land on
# ``2 ** ((k + 1/2) / K)``, which no ratio of two integers can equal, so no
# program can straddle an edge however its ratio was rounded.  And every tick
# names a bin centre, so "2x" on the axis is written under the bars it
# describes.  (The interaction grid used to *start* at 1x instead, so that no
# bucket reached below the smallest possible ratio; that put every pile-up on
# an edge and anchored the two histograms' grids differently, which was more
# confusing than the half-bin of empty axis it saved.)
IMPR_BINS_PER_OCTAVE = 3
# Bars fill this much of their bin, leaving a gutter between bins wide enough to
# read the bars within one as a group.
IMPR_BAR_FILL = 0.75


def improvement_bins(lo, hi):
    """Geometric bin edges covering ``[lo, hi]``.

    Each bin is a factor of ``2 ** (1 / IMPR_BINS_PER_OCTAVE)`` wide, and the
    grid is offset half a bin so every power of two sits at a bin's centre.
    """
    k_per_octave = IMPR_BINS_PER_OCTAVE
    off = -0.5
    k = np.arange(math.floor(math.log2(lo) * k_per_octave - off),
                  math.ceil(math.log2(hi) * k_per_octave - off) + 1)
    edges = 2.0 ** ((k + off) / k_per_octave)
    # The floor/ceil above should cover the data, but they are computed through
    # logs and the callers assert that every program lands in a bin; a value
    # sitting exactly on the last edge must not be rounded outside it.
    step = 2.0 ** (1 / k_per_octave)
    if edges[0] > lo:
        edges = np.insert(edges, 0, edges[0] / step)
    if edges[-1] < hi:
        edges = np.append(edges, edges[-1] * step)
    return edges


def improvement_histogram(collected, groups, key, summarize):
    """Bin every group's ratios onto one shared grid.

    Returns ``(ratios, edges, shares)``, where ``shares[group]`` is that
    benchmark's fraction of programs per bin.  Split out from the plotting so
    ``--paired`` can measure both quantities before drawing either.
    """
    ratios = {g: np.asarray(summarize(collected[g][key])["ratios_overall"])
              for g in groups}
    edges = improvement_bins(min(r.min() for r in ratios.values()),
                             max(r.max() for r in ratios.values()))
    shares = {}
    for group, r in ratios.items():
        counts, _ = np.histogram(r, bins=edges)
        # The grid is built to span the data; anything outside would be
        # silently dropped from a figure that reads as a whole population.
        assert counts.sum() == len(r), (group, counts.sum(), len(r))
        shares[group] = counts / len(r)
    return ratios, edges, shares


def improvement_ylim(edges, shares):
    """Top of the y axis: headroom so the upper-right legend never covers a bar.

    Only the bars the legend sits over constrain it, which is why this is not
    just a margin above the tallest bar overall: for both quantities that one is
    the unimproved bar on the far left, and reserving room above *it* would
    waste a third of the panel.  With --include-bcp the two coincide -- BCP's
    mass is at the right edge -- and the axis does then run well past the
    tallest bar.
    """
    heights = np.max(list(shares.values()), axis=0)
    centers = np.sqrt(edges[:-1] * edges[1:])
    under_legend = centers > math.sqrt(edges[0] * edges[-1])
    return max(heights.max() * 1.15, heights[under_legend].max() / 0.65)


def plot_improvement_hist(collected, groups, key, summarize, xlabel,
                          filename, outdir, paired_side=None, ylim=None):
    """Histogram of per-program improvement factor, benchmarks side by side.

    Same population and same quantity as ``plot_improvement_cdf`` -- this is the
    density the CDF integrates.  Bars are fractions of each benchmark's own
    population rather than counts, since the populations differ by an order of
    magnitude (757 GQA programs against 52 AgentDojo ones) and raw counts would
    only show that.  Every benchmark is binned on one shared grid, so a bar is
    comparable to the bar beside it -- and since the bins are geometric, so is
    every bar to the bars either side of it.

    ``paired_side`` suppresses whichever furniture the *other* panel carries
    when the two histograms are printed next to each other; see PAIRED_SIDE.
    It hides by making things transparent rather than by removing them, so the
    axes keep the extents ``tight_layout`` reserves space for and the two
    figures place their plotting area at exactly the same spot.

    ``ylim`` is the y limit shared across the pair, and main() always passes it,
    paired or not: the two histograms get compared to each other whether or not
    they were drawn into one figure.  Falling back to a per-figure limit is kept
    only for calling this directly.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE_DIST)
    ratios, edges, shares = improvement_histogram(collected, groups, key,
                                                  summarize)
    slowest = min(r.min() for r in ratios.values())
    # Geometric, so a "centre" is midway along the bar as drawn, not in value.
    span = edges[1:] / edges[:-1]
    # The bin holding 1x; 1x is a bin centre, so it is never itself an edge.
    unchanged = int(np.searchsorted(edges, 1.0)) - 1

    bars = []
    for i, group in enumerate(groups):
        r, share = ratios[group], shares[group]
        # Dodging is geometric too: each series takes a 1/n slice of the bin's
        # *log* width, so on the drawn axis every bar comes out the same width.
        # The gutter is taken off the group as a whole rather than off each bar,
        # so a bin's bars touch and only the bins are separated -- which is the
        # whole point of the gutter, since bars that belong together should not
        # be as far apart as bars that do not.
        start = (1 - IMPR_BAR_FILL) / 2
        left = edges[:-1] * span ** (start + IMPR_BAR_FILL * i / len(groups))
        right = edges[:-1] * span ** (start + IMPR_BAR_FILL * (i + 1) / len(groups))
        bars.append(ax.bar(left, share, width=right - left, align="edge",
                           color=GROUP_COLOR[group], alpha=ALPHA, linewidth=0,
                           label=ao.DISPLAY_NAME[group]))
        print(f"  {group}: {len(r)} programs, {share[unchanged]:0.3f} in the "
              f"1x bucket [{edges[unchanged]:0.3f}, {edges[unchanged + 1]:0.3f}), "
              f"tallest other {np.delete(share, unchanged).max():0.3f}")

    figure_style.assert_face_colors(
        [patch for container in bars for patch in container],
        [GROUP_COLOR[group] for group in groups], "histogram bars")
    ax.set_ylim(0, ylim if ylim is not None else improvement_ylim(edges, shares))
    configure_ratio_axis(ax, edges[0], edges[-1], pad=1.04,
                         regressions=slowest < REGRESSION_FLOOR)
    ax.set_xlabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE)
    ax.set_ylabel("Fraction of Programs", fontsize=AXIS_LABEL_FONTSIZE)
    ax.tick_params(labelsize=TICK_FONTSIZE_DIST)
    # Fixed to the corner the headroom above is calculated for.
    legend = ax.legend(handles=bars, fontsize=LEGEND_FONTSIZE, loc="upper right")
    ax.grid(True, axis="y", linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)
    hide_frame(ax)

    # Everything below is hidden by going transparent, never by set_visible or
    # by not drawing it.  An artist that is still present still has an extent,
    # and tight_layout reserves the same margin for it, which is what keeps the
    # two panels' plotting areas in the same place -- the whole point, since
    # they are printed as one figure and any drift shows up as a misalignment.
    if paired_side == "right":
        ax.yaxis.label.set_alpha(0)
        for label in ax.get_yticklabels():
            label.set_alpha(0)
        ax.tick_params(axis="y", color="none")
    elif paired_side == "left":
        legend.get_frame().set_alpha(0)
        for text in legend.get_texts():
            text.set_alpha(0)
        for handle in legend.legend_handles:
            handle.set_alpha(0)

    fig.tight_layout()
    fig.savefig(os.path.join(outdir, filename))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--outdir", default="/tmp",
                    help="directory to write the PDFs into (default: /tmp)")
    ap.add_argument("--mismatches", action="store_true",
                    help="list programs where Python and Quasar disagreed")
    ap.add_argument("--include-bcp", action="store_true",
                    help="also draw BCP in both figures")
    ap.add_argument("--improved-only", action="store_true",
                    help="restrict the scatter and the heatmaps to the programs "
                         "Quasar improved; the paper draws every program")
    ap.add_argument("--cdf", action="store_true",
                    help="also write the CDF of each distribution; the paper "
                         "carries the histograms, so run_all.sh omits these")
    ap.add_argument("--paired", action="store_true",
                    help="draw the two histograms to sit side by side: one y "
                         "axis and one legend between them, on a shared y scale")
    args = ap.parse_args()

    figure_style.use_paper_font()
    os.makedirs(args.outdir, exist_ok=True)
    collected = {group: ao.collect_group(group) for group in ao.GROUPS}
    extra = list(OPTIONAL_GROUPS) if args.include_bcp else []
    scatter_groups = [g for g in collected if g not in OPTIONAL_GROUPS] + extra
    interaction_groups = list(INTERACTION_GROUPS) + extra

    for group, data in collected.items():
        print(f"# {group}: total={data['n_total']} py_succ={data['n_succ_py']} "
              f"epic_succ={data['n_succ_epic']} epic_missing={data['n_missing_epic']}")
        if args.mismatches:
            for prog_id, py_val, epic_val in data["mismatches"]:
                print(f"  Mismatch in {prog_id}: py={py_val!r}, epic={epic_val!r}")

    only_improved = args.improved_only
    plot_speedup(collected, args.outdir, scatter_groups,
                 only_improved=only_improved)

    print("==== ROUNDIMPR")
    for group, data in collected.items():
        print(fmt_summary(group, ao.summarize_interactions(data["interactions"])))

    grids = {}
    for group in interaction_groups:
        grid, n, n_clipped, n_undrawn = interaction_grid(collected, group,
                                                         only_improved)
        grids[group] = grid
        note = (f", {n_undrawn} below {HIST_MIN} left undrawn (grid sums to "
                f"{grid.sum():0.3f})" if n_undrawn else "")
        print(f"  {group}: {n} programs, {n_clipped} clipped into the "
              f"{HIST_MAX}+ row/column{note}")

    plot_interactions(grids, "round_improvement.pdf", args.outdir)

    # All four figures draw the same series, so they share one group list rather
    # than taking the scatter's and the heatmap's separately.  Unlike the
    # heatmap, --include-bcp reads well here: a ratio is scale-free and the axis
    # is logarithmic, so BCP's order-of-magnitude larger interaction counts land
    # as their own group of bars around 32x rather than clipping into the corner
    # the heatmap puts them in.
    print("==== IMPROVEMENT DISTRIBUTIONS")
    # One y limit across the pair, measured before anything is drawn.  Taking
    # the larger of the two keeps every bar inside its panel.
    #
    # Applied whether or not --paired: the two histograms are read side by side
    # in the paper regardless of whether they were drawn into one figure, and a
    # bar that is taller in one panel than another must mean a larger fraction.
    # Left to themselves the two pick scales about 12% apart, which is close
    # enough to look deliberate and wrong enough to misread.
    shared_ylim = max(
        improvement_ylim(*improvement_histogram(
            collected, interaction_groups, key, summarize)[1:])
        for _, key, summarize, _ in QUANTITIES)
    print(f"  shared y limit {shared_ylim:0.4f}")

    for stem, key, summarize, xlabel in QUANTITIES:
        if args.cdf:
            print(f"  -- {stem} CDF")
            plot_improvement_cdf(collected, interaction_groups, key, summarize,
                                 xlabel, f"{stem}_cdf.pdf", args.outdir)
        print(f"  -- {stem} histogram")
        plot_improvement_hist(collected, interaction_groups, key, summarize,
                              xlabel, f"{stem}_hist.pdf", args.outdir,
                              paired_side=PAIRED_SIDE[stem] if args.paired else None,
                              ylim=shared_ylim)


if __name__ == "__main__":
    main()
