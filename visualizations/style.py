"""Shared matplotlib styling for ContextPilot AI visualizations.

Palette follows the project's validated design-system reference (see
`references/palette.md` in the dataviz skill): a fixed-order categorical
theme, a single-hue sequential ramp for magnitude, and a reserved status
palette for good/warning/critical states. Colors are never picked ad hoc —
always pull from the roles below so charts read as one system.
"""
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# --- Categorical theme (fixed order — never cycled arbitrarily) -----------
CATEGORICAL = {
    "blue": "#2a78d6",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
    "magenta": "#e87ba4",
    "orange": "#eb6834",
}
CATEGORICAL_ORDER = ["blue", "aqua", "yellow", "green", "violet", "red", "magenta", "orange"]

# --- Sequential (single hue, light -> dark), for pure magnitude ------------
SEQUENTIAL_BLUE = {
    100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef",
    300: "#6da7ec", 350: "#5598e7", 400: "#3987e5", 450: "#2a78d6",
    500: "#256abf", 550: "#1c5cab", 600: "#184f95", 650: "#104281", 700: "#0d366b",
}

# --- Status palette (reserved — never reused as a generic series color) ---
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

# --- Chart chrome & ink (light mode) ---------------------------------------
CHROME = {
    "surface": "#fcfcfb",
    "page": "#f9f9f7",
    "ink_primary": "#0b0b0b",
    "ink_secondary": "#52514e",
    "ink_muted": "#898781",
    "gridline": "#e1e0d9",
    "baseline": "#c3c2b7",
}

FONT_FAMILY = ["Segoe UI", "DejaVu Sans", "Arial", "sans-serif"]


def apply_style() -> None:
    """Applies the shared look (fonts, spines, gridlines, ticks) to the
    current matplotlib rcParams. Call once at the top of each script."""
    plt.rcParams.update({
        "figure.facecolor": CHROME["page"],
        "axes.facecolor": CHROME["surface"],
        "savefig.facecolor": CHROME["page"],
        "font.family": FONT_FAMILY,
        "font.size": 11,
        "text.color": CHROME["ink_primary"],
        "axes.edgecolor": CHROME["baseline"],
        "axes.labelcolor": CHROME["ink_secondary"],
        "axes.titlecolor": CHROME["ink_primary"],
        "axes.titleweight": "bold",
        "axes.titlesize": 14,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": CHROME["gridline"],
        "grid.linewidth": 0.8,
        "xtick.color": CHROME["ink_muted"],
        "ytick.color": CHROME["ink_muted"],
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.frameon": False,
        "legend.fontsize": 9.5,
    })


def strip_spines(ax, keep=("bottom",)) -> None:
    for side, spine in ax.spines.items():
        spine.set_visible(side in keep)
    if "bottom" in keep:
        ax.spines["bottom"].set_color(CHROME["baseline"])
    ax.grid(axis="x", visible=False)
