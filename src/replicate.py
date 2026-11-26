"""Reproduce two numbers from the Momentum Lab post to check that our data matches theirs."""

import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]


def streak_before(good):
    """Number of good plays in a row just before each play."""
    out, run = np.zeros(len(good), dtype=int), 0
    for i, g in enumerate(good.to_numpy()):
        out[i] = run
        run = run + 1 if g else 0
    return pd.Series(out, index=good.index)


if __name__ == "__main__":
    p = pd.read_parquet(ROOT / "data" / "plays.parquet")

    # Post: 775,689 plays; a good play follows 2 / 3 / 4 / 5+ good plays 45% / 46% / 46% / 47% of the time.
    q = p[p.play_type.isin(["run", "pass"]) & p.epa.notna() & p.down.notna()].copy()
    q["good"] = q.epa > 0
    q["streak"] = q.groupby(["game_id", "posteam", "fixed_drive"]).good.transform(streak_before).clip(upper=5)
    print(f"{len(q):,} plays")
    print(q[q.streak >= 2].groupby("streak").good.mean().round(3).to_dict())

    # Post: the next drive scores 41.7% of the time after a takeaway or stop, 32.9% after a punt.
    d = (
        p[p.posteam.notna() & p.fixed_drive.notna()]
        .groupby(["game_id", "fixed_drive"], sort=False)
        .agg(result=("fixed_drive_result", "first"))
        .reset_index()
        .sort_values(["game_id", "fixed_drive"])
    )
    d["prev"] = d.groupby("game_id").result.shift(1)
    d["scores"] = d.result.isin(["Touchdown", "Field goal"])
    stop = ["Turnover", "Turnover on downs", "Missed field goal", "Opp touchdown"]
    for name, mask in (("takeaway or stop", d.prev.isin(stop)), ("punt", d.prev == "Punt")):
        print(f"after a {name}: {d[mask].scores.mean():.3f} of {mask.sum():,} drives score")
