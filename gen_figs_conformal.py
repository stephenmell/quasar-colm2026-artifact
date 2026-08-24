"""Generate the conformal-calibration boxplots.

Usage:
    uv run python gen_figs_conformal.py             # both datasets, PDFs to /tmp
    uv run python gen_figs_conformal.py gqa         # just one
    uv run python gen_figs_conformal.py -o figs/

Produces:
    conformal.pdf   test error (left) beside uncertain-prediction rate (right)

Each panel carries one box per dataset, so both datasets share a single figure.
Naming a subset of datasets draws only those series.
"""

import os
import argparse

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import analysis_conformal as ac
import figure_style


tick_fontsize = 18
axis_label_fontsize = 20
line_width = 2.5
box_linewidth = 2
fliersize = 8

target_line_color = "#d62728"

# Slack added at each end of the 0..1 axis, in data units.  Roughly ten times
# half a box stroke, so nothing drawn at a limit gets clipped.
X_PAD = 0.02

# Gap between the two panels, expressed on the shared x scale -- 0.2 makes it
# one tick step wide, the same distance as 0.8 to 1.0 within a panel.
PANEL_GAP = 0.2

# figure_style.group_color is the single definition, and takes this module's
# "ad" spelling as well as analysis_opportunistic's "agentdojo".
GROUP_COLOR = {d: figure_style.group_color(d) for d in ac.DATASETS}


def make_grid_box(ax):
    ax.grid(True, which='major', axis='x', linestyle='--', linewidth=1.5, alpha=0.7)

    # No frame: the dashed x grid already carries the scale, and a spine at
    # x=0/x=1 would sit on top of any box edge landing exactly on the limit.
    for spine in ax.spines.values():
        spine.set_visible(False)


def draw_boxes(ax, series, xlabel, target=None):
    """One horizontal box per (label, colour, distribution) in ``series``."""
    labels = [label for label, _, _ in series]
    values = [v for _, _, dist in series for v in dist]
    groups = [label for label, _, dist in series for _ in dist]
    palette = {label: color for label, color, _ in series}

    sns.boxplot(
        x=values,
        y=groups,
        order=labels,
        hue=groups,
        hue_order=labels,
        palette=palette,
        # Seaborn's categorical plots default to saturation=0.75, which quietly
        # desaturates whatever palette they are handed -- #1f77b4 renders as
        # #3274a1 and #ff7f0e as #e1812c, so these boxes came out a visibly
        # different blue and orange from the matplotlib-drawn figures next to
        # them.  1 means "the colour I asked for".
        saturation=1,
        legend=False,
        width=0.5,
        linewidth=box_linewidth,
        fliersize=fliersize,
        flierprops=dict(marker='o', markerfacecolor='black', markeredgecolor='black',
                        markersize=fliersize, markeredgewidth=2),
        # No outline on the box itself, so the only strokes are the whiskers,
        # their caps, and the median.  The median is then the sole line touching
        # the fill, which is what makes it readable even when it coincides with
        # a quartile -- as it does for AgentDojo, whose quartiles saturate.
        boxprops=dict(linewidth=0),
        ax=ax,
        orient="h",
    )
    # seaborn desaturated these once already; ax.patches is the boxes.
    figure_style.assert_face_colors(ax.patches, palette.values(),
                                    "conformal boxes")
    if target is not None:
        ax.axvline(target, linestyle="--", linewidth=line_width,
                   color=target_line_color)
    # Padded past [0, 1] so that a box edge landing exactly on 0 or 1 -- which
    # happens whenever a quartile saturates -- is drawn at full width instead of
    # having half its stroke clipped away at the axes boundary.
    ax.set_xlim(-X_PAD, 1 + X_PAD)
    # The y axis now names the dataset, so unlike the old one-box-per-figure
    # version its labels carry information and are kept.
    ax.tick_params(axis="y", labelsize=axis_label_fontsize)
    # Set ticks explicitly: the padding would otherwise pull in ticks beyond
    # [0, 1], and the data is a fraction, so there is nothing out there.
    ticks = list(np.arange(0, 1.01, 0.2))
    ax.set_xticks(ticks + ([target] if target is not None else []))
    ax.tick_params(axis="x", labelsize=tick_fontsize)
    ax.set_xlabel(xlabel, fontsize=axis_label_fontsize)
    if target is not None:
        # Colour only the target tick
        for label in ax.get_xticklabels():
            if np.isclose(float(label.get_text()), target, atol=1e-3):
                label.set_color(target_line_color)
    sns.despine(ax=ax, left=True)
    make_grid_box(ax)


def plot_conformal(err_series, unk_series, path, target=None):
    """Both metrics side by side: error on the left, uncertainty on the right."""
    n = max(len(err_series), len(unk_series))
    fig, axes = plt.subplots(1, 2, sharey=True,
                             figsize=figure_style.scaled((14, 1.2 + 0.9 * n)))
    draw_boxes(axes[0], err_series, "Test Error", target=target)
    draw_boxes(axes[1], unk_series, "Fraction of Predictions Uncertain")
    fig.tight_layout()
    # ``wspace`` is measured in axes widths, and each axes spans 1 + 2 * X_PAD
    # on the x scale, so this ratio lands the gap at exactly PANEL_GAP there.
    # Applied after tight_layout, which would otherwise overwrite it.
    fig.subplots_adjust(wspace=PANEL_GAP / (1 + 2 * X_PAD))
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("datasets", nargs="*", choices=list(ac.DATASETS), default=None,
                    help="datasets to plot (default: all)")
    ap.add_argument("-o", "--outdir", default="/tmp",
                    help="directory to write the PDFs into (default: /tmp)")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="print per-task and per-split detail")
    args = ap.parse_args()

    figure_style.use_paper_font()
    os.makedirs(args.outdir, exist_ok=True)
    datasets = args.datasets or list(ac.DATASETS)

    results = {}
    for dataset in datasets:
        res = ac.compute(dataset, verbose=args.verbose)
        results[dataset] = res
        print(f"==== {res['label']}")
        print(f"error\t{res['err'][0]:0.3f}\t{res['err'][1]:0.3f}")
        print(f"unk\t{res['unk'][0]:0.3f}\t{res['unk'][1]:0.3f}")

    def series(key):
        return [(results[d]["label"], GROUP_COLOR[d], results[d][key])
                for d in datasets]

    # Every dataset calibrates against the same target, so one line serves the
    # whole figure; assert rather than silently draw the first dataset's.
    targets = {results[d]["test_target"] for d in datasets}
    assert len(targets) == 1, f"datasets disagree on the target: {targets}"

    plot_conformal(series("err_dist"), series("unk_dist"),
                   os.path.join(args.outdir, "conformal.pdf"),
                   target=targets.pop())


if __name__ == "__main__":
    main()
