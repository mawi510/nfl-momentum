"""Draw the four main tests, explore and confirm, into results/main_tests.png."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from features import ROOT

SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SAMPLES = [("explore", "2006-2019 (explore)", "#2a78d6", 0.16), ("confirm", "2020-2025 (confirm)", "#eb6834", -0.16)]
ROWS = {
    "H1": "H1  Next drive after a missed\ndeep throw, minus after a made one",
    "H2": "H2  Drop after a big loss\nminus rise after a big gain",
    "H3": "H3  Drive after 3+ bad drives\nthen a good one",
    "H4": "H4  Next play goes to the same side,\nafter success minus after failure",
}


def panel(ax, hyps, scale, minimum, xlabel, predicted):
    ax.axvspan(-minimum, minimum, color=GRID, alpha=0.6, lw=0)
    ax.axvline(0, color=MUTED, lw=1)
    for name, label, color, offset in SAMPLES:
        r = pd.read_csv(ROOT / "results" / f"{name}.csv")
        r = r[(r.role == "main") & (r.subset == "all")].set_index("hypothesis")
        for i, h in enumerate(hyps):
            y = -i + offset
            ax.plot([r.low[h] * scale, r.high[h] * scale], [y, y], color=color, lw=2, solid_capstyle="round")
            ax.plot(r.effect[h] * scale, y, "o", color=color, ms=8, mec=SURFACE, mew=2, label=label if i == 0 else None)
    for i, h in enumerate(hyps):
        ax.annotate(predicted[h], (1.0, -i), xycoords=("axes fraction", "data"), xytext=(-4, 0),
                    textcoords="offset points", ha="right", va="center", fontsize=8.5, color=MUTED)
    ax.set_yticks([-i for i in range(len(hyps))], [ROWS[h] for h in hyps], fontsize=10, color=INK)
    ax.set_ylim(-len(hyps) + 0.45, 0.55)
    ax.set_xlabel(xlabel, fontsize=9.5, color=MUTED)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9, length=0)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ax.spines.values():
        side.set_visible(False)


if __name__ == "__main__":
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(9.5, 6.4), height_ratios=[3, 1.15], facecolor=SURFACE)
    for ax in (top, bottom):
        ax.set_facecolor(SURFACE)
    panel(top, ["H1", "H2", "H3"], 1, 0.02, "EPA above expected per play, real result minus shuffled games", 
          {"H1": "momentum predicts left", "H2": "our idea predicts right", "H3": "momentum predicts right"})
    top.set_xlim(-0.065, 0.065)
    panel(bottom, ["H4"], 100, 1, "Percentage points, real result minus shuffled games", {"H4": "predicts right"})
    bottom.set_xlim(-6.5, 6.5)
    top.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2, frameon=False, fontsize=9.5, labelcolor=INK, handletextpad=0.3)
    fig.suptitle("Four tests for momentum in NFL play-by-play: none holds up as predicted", x=0.02, ha="left", fontsize=13, color=INK, weight="bold")
    fig.text(0.02, 0.01, "Dots are effects; lines are 95% intervals from 2,000 within-game shuffles. Gray band: smaller than our minimum size "
             "(0.02 EPA per play, 1 point).\nH2 clears the band on the wrong side: the next drive is slightly better after a big play of either sign.",
             fontsize=8.5, color=MUTED, va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 0.97))
    fig.savefig(ROOT / "results" / "main_tests.png", dpi=180, facecolor=SURFACE)
