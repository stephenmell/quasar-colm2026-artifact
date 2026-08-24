"""Shared figure styling: draw in the same typeface as the paper.

This is a library.  Entry points call ``use_paper_font()`` from ``main()``
rather than at import time, so importing it has no side effects.

The paper sets Palatino -- ``colm2026_conference.sty`` loads ``mathpazo``, and
the built PDF embeds URW Palladio L.  Matplotlib defaults to DejaVu Sans, which
made the figures the one part of a page in a different typeface; ``pdffonts
main.pdf`` showed it plainly, DejaVu Sans being the only Type 3 entries in the
document and every one of them a figure.

Matching it needs no LaTeX at figure-generation time.  TeX Gyre Pagella is the
Palatino clone TeX Live ships as OTF, so on any machine that can build the paper
matplotlib can draw in the same face the paper will typeset in.  The rest of
``PAPER_FONTS`` is fallback for machines without it, in descending order of
fidelity: two more Palatino clones, the real thing if someone has it licensed,
and finally EB Garamond -- not Palatino, but an old-style serif that sits beside
it far better than a sans does.  ``use_paper_font`` reports which one it found
so a reviewer regenerating the figures can see when they are getting a
substitute rather than wondering why their PDFs look unlike the paper's.

No label in any figure uses mathtext, so ``mathtext.*`` is deliberately left
alone: pointing it at a text face that lacks the math glyphs buys a warning and
nothing else.  A label that grows a ``$`` needs that set here too.

Verify a change here by rendering, not by reading: ``pdffonts`` on an output PDF
names the face that actually got embedded and warns if the embedding is
malformed, which is how the ``pdf.fonttype`` choice below was settled.
"""

import matplotlib
from matplotlib import font_manager


# Every figure is included at a fixed width, so LaTeX scales it by
# width/figwidth.  Font sizes are in points and do not take part in that, which
# means a *smaller* figure yields *larger* type on the page: shrinking both
# dimensions by k multiplies the rendered text size by 1/k while leaving the
# on-page height unchanged (k*H * L/(k*W) == H * L/W).  So this is a pure
# text-size knob, not a layout one -- raise it to make labels, ticks and legends
# bigger without touching a single fontsize.
#
# It scales everything measured in points, not just text: line widths, marker
# sizes and tick lengths grow by the same factor, which is what keeps a figure
# looking like itself rather than like a thin-lined drawing with big labels.
TEXT_SCALE = 1.15


def scaled(figsize):
    """A figure size shrunk so its point-sized elements render TEXT_SCALE bigger."""
    return tuple(dimension / TEXT_SCALE for dimension in figsize)


# One hue per benchmark, for every figure in the paper.  This lives here rather
# than in a generator because both generators need it and a colour that means
# one benchmark in one figure and another in the next is worse than no colour
# coding at all.  Import it; do not restate it.
#
# These are matplotlib's first three default-cycle colours.  Checked with the
# dataviz palette validator: CVD separation dE 24.6 (target 8.0), normal-vision
# dE 35.7 (floor 15.0).
BASE_GROUP_COLOR = {"gqa": "#1f77b4", "agentdojo": "#ff7f0e", "bcp": "#2ca02c"}

# The figures are drawn a shade lighter than those base hues.  That look came
# about by accident -- the bar charts and the scatter were drawn at alpha 0.8,
# which composites against the page -- and it is worth keeping, but not by
# keeping the alpha: an alpha'd mark renders a colour that depends on what is
# behind it, so overlapping marks darken, a mark over a gridline differs from
# one over blank page, and the whole figure changes if it is ever placed on a
# tinted background.  Compositing once, here, gives the same appearance as a
# flat opaque colour that renders identically everywhere -- and keeps
# assert_face_colors meaningful, since what is asked for is what appears.
PAGE_COLOR = "#ffffff"
SERIES_TINT = 0.8


def _composite(colour, alpha, background):
    """``colour`` at ``alpha`` over ``background``, as an opaque colour."""
    from matplotlib.colors import to_hex, to_rgb

    fg, bg = to_rgb(colour), to_rgb(background)
    return to_hex(tuple(alpha * f + (1 - alpha) * b for f, b in zip(fg, bg)))


GROUP_COLOR = {group: _composite(colour, SERIES_TINT, PAGE_COLOR)
               for group, colour in BASE_GROUP_COLOR.items()}

# analysis_conformal calls AgentDojo "ad"; analysis_opportunistic calls it
# "agentdojo".  Rather than make either rename its datasets, map the aliases
# here so both can ask for a colour by whatever name they already use.
GROUP_ALIAS = {"ad": "agentdojo"}


def group_color(group):
    """The paper's colour for a benchmark, under either module's naming."""
    return GROUP_COLOR[GROUP_ALIAS.get(group, group)]


# Series marks are drawn at full opacity.  Alpha is tempting for overplotting,
# but it composites against the page and so renders a *different* colour from
# the one asked for -- 0.8 turns #1f77b4 into #4b92c3 -- which is invisible
# within one figure and glaring when a bar chart sits beside a box plot using
# the same nominal hue.  Anything that needs to show density should do it with
# mark size or binning, not opacity.
SERIES_ALPHA = 1.0


def assert_face_colors(artists, expected, context):
    """Fail unless every artist is filled with exactly one of ``expected``.

    Read back from the artists after drawing rather than trusting the arguments
    passed in, because the two ways this has actually broken were both a library
    quietly transforming the colour on its way to the canvas:

    * seaborn's categorical plots default to ``saturation=0.75``, which drew
      #1f77b4 as #3274a1;
    * ``alpha=0.8`` composites against the page, rendering #1f77b4 as #4b92c3.

    Neither is visible within a single figure -- both look like a perfectly
    reasonable blue -- and both are obvious the moment that figure is printed
    beside another one using the nominal hue.  Checking the request rather than
    the result would have caught neither.
    """
    from matplotlib.colors import to_hex, to_rgba

    allowed = {to_rgba(colour) for colour in expected}
    bad = set()
    for artist in artists:
        faces = artist.get_facecolor()
        # A collection returns an (n, 4) array; a patch returns a single tuple.
        faces = faces if getattr(faces, "ndim", 1) == 2 else [faces]
        for face in faces:
            rgba = tuple(float(v) for v in face)
            if rgba not in allowed:
                bad.add(rgba)
    if bad:
        raise AssertionError(
            f"{context}: drawn in {sorted(to_hex(c, keep_alpha=True) for c in bad)}, "
            f"expected {sorted(to_hex(c, keep_alpha=True) for c in allowed)} "
            f"-- a library transformed the colour (seaborn saturation, or alpha "
            f"compositing); see figure_style.assert_face_colors")


# In descending order of how closely each matches what the paper embeds.
PAPER_FONTS = (
    "TeX Gyre Pagella",   # TeX Live's Palatino clone; what the paper resolves to
    "P052",               # URW's Palatino clone, from urw-base35
    "URW Palladio L",     # the same family under its pre-2016 name
    "Palatino",
    "Palatino Linotype",
    "EB Garamond",        # not Palatino, but the right century
)


def use_paper_font():
    """Set matplotlib's default face to the paper's.  Returns the name used.

    Returns ``None`` if none of ``PAPER_FONTS`` is installed, in which case
    matplotlib falls back to its own default serif and the figures still render
    -- just not in the paper's face.  Either way it says which on stdout, beside
    the statistics the generators already print: a silent substitution is the
    kind of thing nobody notices until the figures are in a draft.
    """
    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((name for name in PAPER_FONTS if name in available), None)

    matplotlib.rcParams["font.family"] = "serif"
    # Matplotlib walks this list and takes the first it can resolve, so the
    # fallback chain is the rcParam rather than anything this module enforces.
    matplotlib.rcParams["font.serif"] = [
        *PAPER_FONTS, *matplotlib.rcParamsDefault["font.serif"]
    ]
    # Type 3, matplotlib's default, pinned rather than left implicit because the
    # obvious upgrade is wrong here.  Setting ``pdf.fonttype`` to 42 normally
    # buys proper embedded outlines and dodges the camera-ready checks that
    # reject Type 3 -- but 42 means TrueType, and every Palatino clone ships as
    # OTF with CFF outlines.  Matplotlib emits the CFF bytes under
    # ``/Subtype /CIDFontType2`` and ``/FontFile2``, which both declare
    # TrueType: the result is a malformed PDF that renders correctly but makes
    # poppler warn, and the warning follows the figure into the paper.  A valid
    # Type 3 beats an invalid Type 42.  If a TrueType Palatino ever turns up,
    # 42 becomes the better choice.
    matplotlib.rcParams["pdf.fonttype"] = 3
    matplotlib.rcParams["ps.fonttype"] = 3

    if chosen is None:
        print(f"# no paper font found ({', '.join(PAPER_FONTS)}); figures will "
              f"use matplotlib's default serif and will not match the paper")
    else:
        print(f"# figures drawn in {chosen}")
    return chosen
