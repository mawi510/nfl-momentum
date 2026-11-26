"""Draw the two charts for MODEL.md into results/."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import beta

from features import ROOT

SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"
GAME = "2025_07_NYG_DEN"


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_axisbelow(True)


def gap_split(p):
    r = pd.read_csv(ROOT / "results" / "model.csv")
    r = r[(r.view == "all seasons") & r.measure.str.startswith("success gap split")]
    r = r.assign(name=r.measure.str.split(": ").str[1]).set_index("name")
    seq = p[p.prev_good.notna()]
    after = seq.groupby("prev_good").good.mean()
    order = ["table", "level that day", "before the game, score and clock", "left over"]
    labels = ["The situation the last play left\n(down, distance, field position)", "How good the offense is that day,\nbeyond what we expected",
              "What we knew before the game,\nplus score and clock", "Left over: any effect of the\nlast play on the next one"]
    fig, ax = plt.subplots(figsize=(9.5, 4.6), facecolor=SURFACE)
    style(ax)
    y = np.arange(len(order))[::-1]
    est = r.estimate[order].to_numpy()
    ax.barh(y, est, height=0.5, color=BLUE)
    ax.hlines(y, r.low[order], r.high[order], color=INK, lw=1.5)
    ax.axvline(0, color=MUTED, lw=1)
    for yi, e, hi in zip(y, est, r.high[order]):
        ax.text(max(hi, 0) + 0.08, yi, f"{e:+.2f} pts  ({100 * e / est.sum():.0f}%)", va="center", fontsize=10, color=INK)
    ax.set_yticks(y, labels, fontsize=10, color=INK)
    ax.set_xlim(-0.4, 6.2)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_xlabel("Percentage points of the gap", fontsize=9.5, color=MUTED)
    fig.suptitle("Success follows success because of the situation it leaves", x=0.02, ha="left", fontsize=13, color=INK, weight="bold")
    fig.text(0.02, 0.905, f"The next play succeeds {after[1]:.1%} of the time after a success and {after[0]:.1%} after a failure. "
             f"Where that {100 * (after[1] - after[0]):.1f} point gap comes from.", fontsize=9.5, color=MUTED)
    fig.text(0.02, 0.01, "NFL regular season 2006-2025, plays that follow another play in the same drive. Each season is measured with tables and models built from "
             "the other 19.\nBlack lines are 95% intervals from resampling games.", fontsize=8.5, color=MUTED, va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 0.9))
    fig.savefig(ROOT / "results" / "gap_split.png", dpi=180, facecolor=SURFACE)


def game_belief(p):
    g = p[p.game_id == GAME].sort_values("play_id").reset_index(drop=True)
    g["x"] = np.arange(1, len(g) + 1)
    quarters = g.groupby("qtr").x.min()
    teams = list(g.posteam.unique())
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 6.2), sharex=True, sharey=True, facecolor=SURFACE)
    for ax, team, color in zip(axes, teams, (BLUE, ORANGE)):
        style(ax)
        t = g[g.posteam == team]
        n, s, e, prior = np.arange(1, len(t) + 1), t.good.cumsum().to_numpy(), t.exp_good.cumsum().to_numpy(), t.n_good.iloc[0]
        center = e / n
        a, b = prior * center + s, prior * (1 - center) + n - s
        x = np.concatenate([[0], t.x.to_numpy(), [len(g)]])
        line = 100 * np.concatenate([[0], (s - e) / (n + prior), [(s[-1] - e[-1]) / (n[-1] + prior)]])
        start = beta.ppf([0.025, 0.975], prior * center[0], prior * (1 - center[0])) - center[0]
        low = 100 * np.concatenate([[start[0]], beta.ppf(0.025, a, b) - center, [beta.ppf(0.025, a[-1], b[-1]) - center[-1]]])
        high = 100 * np.concatenate([[start[1]], beta.ppf(0.975, a, b) - center, [beta.ppf(0.975, a[-1], b[-1]) - center[-1]]])
        ax.fill_between(x, low, high, step="post", color=color, alpha=0.15, lw=0)
        ax.step(x, line, where="post", color=color, lw=2)
        ax.axhline(0, color=MUTED, lw=1)
        for q, qx in quarters.items():
            if q > 1:
                ax.axvline(qx - 0.5, color=GRID, lw=1)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_title(f"{team} offense: {int(s[-1])} successes on {len(t)} plays, {e[-1]:.1f} expected. Belief at the end: {line[-1]:+.1f} points", loc="left", fontsize=10.5, color=INK)
        ax.set_ylabel("Success rate above\nexpected, points", fontsize=9, color=MUTED)
        print(team, "plays", len(t), "successes", int(s[-1]), "expected", round(e[-1], 1), "final belief", round(line[-1], 2), "band", round(low[-1], 1), round(high[-1], 1),
              "| 4th quarter:", int(t[t.qtr == 4].good.sum()), "of", int((t.qtr == 4).sum()), "expected", round(t[t.qtr == 4].exp_good.sum(), 1))
    for q, qx in quarters.items():
        axes[0].text(qx + 1, axes[0].get_ylim()[1] * 0.86, f"Q{int(q)}" if q <= 4 else "OT", fontsize=9, color=MUTED)
    axes[1].set_xlabel("Play of the game", fontsize=9.5, color=MUTED)
    fig.suptitle("Denver scored 33 in the fourth quarter. Our belief about its offense rose by 0.7 points.", x=0.02, ha="left", fontsize=13, color=INK, weight="bold")
    fig.text(0.02, 0.01, "Giants at Broncos, 2025 week 7. Denver scored 33 points in the fourth quarter and won 33-32. Line: our belief about the offense's success rate that day,\n"
             "compared with what we expected before the game. Shaded: 95% credible band. Prior and expected rates are built from the other 19 seasons.", fontsize=8.5, color=MUTED, va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(ROOT / "results" / "game_belief.png", dpi=180, facecolor=SURFACE)


if __name__ == "__main__":
    p = pd.read_parquet(ROOT / "data" / "plays_cv.parquet").sort_values(["team_game", "fixed_drive", "play_id"], ignore_index=True)
    p["prev_good"] = p.groupby(["team_game", "fixed_drive"]).good.shift(1)
    gap_split(p)
    game_belief(p)
