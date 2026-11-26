"""Size the situation chain: how much of "success follows success" comes only from the down, distance, and field position that a play leaves behind?

Exploratory, 2006-2019 only. The chain is a table: for each situation, how often the next play
succeeds, is a pass, or is a sack or turnover. It knows nothing about what happened earlier.
"""

import numpy as np
import pandas as pd

from features import EXPLORE, ROOT

STATE = ["down", "dist", "zone"]


def add_state(p):
    p = p.sort_values(["team_game", "fixed_drive", "play_id"]).copy()
    p["dist"] = p.ydstogo.clip(upper=16)
    p["zone"] = pd.cut(p.yardline_100, [0, 10, 20, 50, 80, 100]).astype(str)
    p["mistake"] = ((p.sack == 1) | (p.interception == 1) | (p.fumble_lost == 1)).astype(int)
    p["prev_good"] = p.groupby(["team_game", "fixed_drive"]).good.shift(1)
    return p


if __name__ == "__main__":
    p = pd.read_parquet(ROOT / "data" / "plays_x.parquet")
    p = add_state(p[p.season.isin(EXPLORE)])
    table = p.groupby(STATE)[["good", "pass", "mistake"]].mean().add_suffix("_chain")
    seq = p[p.prev_good.notna()].join(table, on=STATE)

    after = seq.groupby("prev_good")
    print("situation the last play left behind:")
    print(f"  1st down:          after success {after.apply(lambda g: (g.down == 1).mean(), include_groups=False)[1]:.0%}, after failure {after.apply(lambda g: (g.down == 1).mean(), include_groups=False)[0]:.0%}")
    print(f"  3rd/4th and 7+:    after success {after.apply(lambda g: ((g.down >= 3) & (g.ydstogo >= 7)).mean(), include_groups=False)[1]:.0%}, after failure {after.apply(lambda g: ((g.down >= 3) & (g.ydstogo >= 7)).mean(), include_groups=False)[0]:.0%}")

    print("next play, after a success against after a failure (real, and what the chain alone predicts):")
    for name, col in (("succeeds", "good"), ("is a pass", "pass"), ("is a sack or turnover", "mistake")):
        real, chain = after[col].mean(), after[f"{col}_chain"].mean()
        gap, chain_gap = real[1] - real[0], chain[1] - chain[0]
        print(f"  {name:22s} real {real[1]:.1%} vs {real[0]:.1%} (gap {100 * gap:+.1f} pts) | chain {chain[1]:.1%} vs {chain[0]:.1%} (gap {100 * chain_gap:+.1f} pts) | left over {100 * (gap - chain_gap):+.1f} pts")

    print("how often the next play succeeds, by situation (the chain's table, a few rows):")
    for down, lo, hi in ((1, 10, 10), (2, 1, 3), (2, 8, 16), (3, 1, 3), (3, 7, 16)):
        s = p[(p.down == down) & p.ydstogo.between(lo, hi)]
        print(f"  down {down}, {lo} to {hi} to go: succeeds {s.good.mean():.0%}, pass {s['pass'].mean():.0%}, sack or turnover {s.mistake.mean():.1%}  ({len(s):,} plays)")
