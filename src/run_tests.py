"""Run every test in HYPOTHESES.md on one sample and write results/<sample>.csv."""

import pathlib
import sys

import numpy as np
import pandas as pd

from features import CONFIRM, EXPLORE, ROOT
from shuffle import label_shuffle, order_shuffle, summarize

N_PERM = 2000
rows = []


def record(hyp, test, role, subset, res, n):
    rows.append({"hypothesis": hyp, "test": test, "role": role, "subset": subset, "n": int(n), **res})


def label_test(ev, label, value, weight, strata):
    """Pooled mean of value after label=True minus after label=False, against shuffled labels."""
    ev = ev.dropna(subset=[value, weight])
    key = ev[strata].astype(str).agg("|".join, axis=1) if isinstance(strata, list) else ev[strata]
    ev = ev[ev.groupby(key)[label].transform("nunique") == 2]
    key = key.loc[ev.index]
    y, w, lab = ev[value].to_numpy(float), ev[weight].to_numpy(float), ev[label].to_numpy(bool)

    def stat(l):
        return y[l].sum() / w[l].sum() - y[~l].sum() / w[~l].sum()

    perm = np.array([stat(l) for l in label_shuffle(key.factorize()[0], lab, N_PERM)])
    return summarize(stat(lab), perm), len(ev)


def after(masks_fn, value, weight, lag=1, close=False):
    """Stat function: sum and count of the outcome on drives that follow each mask."""
    def fn(m):
        y, w = m[value][:, lag:], m[weight][:, lag:]
        ok = m["close"][:, lag:] if close else np.ones(y.shape, bool)
        return np.array([[y[k & ok].sum(), w[k & ok].sum()] for k in masks_fn(m)])
    return fn


def tag_masks(col, tags):
    return lambda m: [np.ones(m[col][:, :-1].shape, bool)] + [m[col][:, :-1] == t for t in tags]


def breakthrough_masks(m):
    bad, good = m["epa"] < 0, m["epa"] > 0
    three = bad[:, :-4] & bad[:, 1:-3] & bad[:, 2:-2]
    return [three & good[:, 3:-1], ~three & good[:, 3:-1], three & bad[:, 3:-1]]


def cluster_gap(d, mask):
    """Mean of win_x on masked drives minus the mean over all drives, with games as the unit."""
    g = d.assign(a=d.win_x * mask, na=mask.astype(float)).groupby("game_id")[["a", "na", "win_x", "one"]].sum()
    gap = g.a.sum() / g.na.sum() - g.win_x.sum() / g.one.sum()
    # Linearized residual per game for the difference of two ratio means.
    r = (g.a - g.na * g.a.sum() / g.na.sum()) / g.na.sum() - (g.win_x - g.one * g.win_x.sum() / g.one.sum()) / g.one.sum()
    se = np.sqrt((r**2).sum())
    from scipy.stats import norm
    return {"observed": g.a.sum() / g.na.sum(), "chance": g.win_x.sum() / g.one.sum(), "effect": gap,
            "low": gap - 1.96 * se, "high": gap + 1.96 * se, "p": 2 * norm.sf(abs(gap / se))}


def drive_tests(d, subset, close=False):
    """All next-drive tests on one set of drives. Only the main tests are run for the check subsets."""
    full = subset == "all"

    def run(tag, tags, value="epa_x", weight="n"):
        return order_shuffle(d, [tag, value, weight, "close"], after(tag_masks(tag, tags), value, weight, close=close), N_PERM)

    # H1: drives with only missed deep throws (1) against drives with only made deep throws (2).
    obs, perm, cnt = run("deep_tag", [1, 2])
    record("H1", "next drive EPA above expected per play, after a missed deep throw minus after a made one", "main", subset,
           summarize(obs[1] - obs[2], perm[:, 1] - perm[:, 2]), cnt[1:].sum())
    if full:
        for i, name in ((1, "missed"), (2, "made")):
            record("H1", f"next drive after a {name} deep throw, against chance", "secondary", subset, summarize(obs[i], perm[:, i]), cnt[i])
        obs, perm, cnt = run("deep_tag", [1, 2], "deep", "att")
        record("H1", "share of next-drive passes that are deep, after a missed deep throw minus after a made one", "secondary", subset,
               summarize(obs[1] - obs[2], perm[:, 1] - perm[:, 2]), cnt[1:].sum())
        obs, perm, cnt = run("erased_tag", [1, 2])
        record("H1", "next drive, after a 20+ yard gain erased by penalty minus after one that stood", "secondary", subset,
               summarize(obs[1] - obs[2], perm[:, 1] - perm[:, 2]), cnt[1:].sum())
        if "ftn_tag" in d:
            f = d[d.season >= 2022]
            obs, perm, cnt = order_shuffle(f, ["ftn_tag", "epa_x", "n", "close"], after(tag_masks("ftn_tag", [1, 2]), "epa_x", "n"), N_PERM)
            record("H1", "next drive, after a dropped or uncaught catchable deep ball minus after a caught one (FTN)", "secondary", "2022-2025",
                   summarize(obs[1] - obs[2], perm[:, 1] - perm[:, 2]), cnt[1:].sum())

    # H2: loss of 2-3 EPA (1), loss of 3+ (2), gain of 2-3 (3), gain of 3+ (4).
    obs, perm, cnt = run("swing_tag", [1, 2, 3, 4])
    asym = lambda m: -(m[..., 1] + m[..., 2] + m[..., 3] + m[..., 4]) / 2
    record("H2", "drop after a loss minus rise after a gain, next drive EPA above expected per play", "main", subset,
           summarize(asym(obs), asym(perm)), cnt[1:].sum())
    if full:
        record("H2", "next drive after a loss of 2+ EPA, against chance", "secondary", subset, summarize(obs[1:3].mean(), perm[:, 1:3].mean(axis=1)), cnt[1:3].sum())
        record("H2", "next drive after a gain of 2+ EPA, against chance", "secondary", subset, summarize(obs[3:5].mean(), perm[:, 3:5].mean(axis=1)), cnt[3:5].sum())
        obs, perm, cnt = run("swing_tag", [1, 2, 3, 4], "first_pass", "one")
        record("H2", "first play of next drive is a pass, after a loss minus after a gain", "secondary", subset,
               summarize(obs[1:3].mean() - obs[3:5].mean(), perm[:, 1:3].mean(axis=1) - perm[:, 3:5].mean(axis=1)), cnt[1:].sum())

    # H3: three or more bad drives, then a good one.
    obs, perm, cnt = order_shuffle(d, ["epa", "epa_x", "n", "close"], after(breakthrough_masks, "epa_x", "n", lag=4, close=close), N_PERM)
    record("H3", "drive after 3+ bad drives then a good one, EPA above expected per play, against chance", "main", subset, summarize(obs[0], perm[:, 0]), cnt[0])
    if full:
        record("H3", "drive after a breakthrough minus drive after an ordinary good drive", "secondary", subset, summarize(obs[0] - obs[1], perm[:, 0] - perm[:, 1]), cnt[0])
        record("H3", "drive after 4+ bad drives in a row, against chance", "secondary", subset, summarize(obs[2], perm[:, 2]), cnt[2])
        by_game = d.groupby("team_game").epa
        brk = (by_game.shift(4) < 0) & (by_game.shift(3) < 0) & (by_game.shift(2) < 0) & (by_game.shift(1) > 0)
        record("H3", "wins above win probability at the start of the drive after a breakthrough", "secondary", subset, cluster_gap(d, brk), brk.sum())


def main(sample):
    seasons = {"explore": EXPLORE, "confirm": CONFIRM}[sample]
    p = pd.read_parquet(ROOT / "data" / "plays_x.parquet")
    p = p[p.season.isin(seasons)].sort_values(["team_game", "fixed_drive", "play_id"], ignore_index=True)
    d = pd.read_parquet(ROOT / "data" / "drives.parquet")
    d = d[d.season.isin(seasons)].sort_values(["team_game", "pos"], ignore_index=True)
    drive_key = ["team_game", "fixed_drive"]

    def tag_drives(bad, good, name):
        """1 = the drive has only the bad event, 2 = only the good event, 0 = neither or both."""
        flags = pd.concat([bad[drive_key].assign(bad=True), good[drive_key].assign(good=True)]).groupby(drive_key)[["bad", "good"]].max()
        j = d[drive_key].join(flags, on=drive_key)
        d[name] = np.select([j.bad.eq(True) & ~j.good.eq(True), j.good.eq(True) & ~j.bad.eq(True)], [1, 2], 0)

    deep = p[(p.air_yards >= 20) & (p.cp >= 0.25)]
    tag_drives(deep[deep.incomplete_pass == 1], deep[deep.complete_pass == 1], "deep_tag")

    raw = pd.read_parquet(ROOT / "data" / "plays.parquet", columns=["season", "game_id", "posteam", "fixed_drive", "play_type", "penalty", "penalty_team", "desc"])
    raw = raw[raw.season.isin(seasons) & (raw.play_type == "no_play") & (raw.penalty == 1) & (raw.penalty_team == raw.posteam)]
    erased = raw[raw.desc.str.extract(r"for (\d+) yards")[0].astype(float) >= 20].copy()
    erased["team_game"] = erased.game_id + "_" + erased.posteam
    tag_drives(erased, p[p.yards_gained >= 20], "erased_tag")

    if sample == "confirm":
        ftn = pd.concat(pd.read_parquet(f) for f in sorted((ROOT / "data" / "raw").glob("ftn_charting_*.parquet")))
        ftn = ftn.rename(columns={"nflverse_game_id": "game_id", "nflverse_play_id": "play_id"})[["game_id", "play_id", "is_drop", "is_catchable_ball"]]
        f = p[p.air_yards >= 20].merge(ftn, on=["game_id", "play_id"])
        tag_drives(f[(f.incomplete_pass == 1) & (f.is_drop | f.is_catchable_ball)], f[f.complete_pass == 1], "ftn_tag")

    loss, gain = d.min_epa <= -2, d.max_epa >= 2
    d["swing_tag"] = np.select([loss & gain, loss & (d.min_epa > -3), loss, gain & (d.max_epa < 3), gain], [0, 1, 2, 3, 4], 0)

    drive_tests(d, "all")
    drive_tests(d, "close", close=True)
    # Long, good drives are more often a team's last drive, so drop it as a check on the shuffle.
    drive_tests(d[d.pos < d.groupby("team_game").pos.transform("max")], "without last drive")

    # ---------- H4: where the ball goes ----------
    p["side"] = np.where(p.play_type == "pass", p.pass_location, p.run_location)
    prev = p.groupby(drive_key)[["good", "play_type", "side"]].shift(1)
    p["prev_good"], p["prev_type"], p["prev_side"] = prev.good == 1, prev.play_type, prev.side
    p["dn"] = p.down.clip(upper=3).astype(int)
    p["dist"] = pd.cut(p.ydstogo, [0, 3, 7, 99]).astype(str)
    p["one"] = 1
    seq = p[p.prev_type.notna()].assign(same_type=lambda x: (x.play_type == x.prev_type).astype(int))
    pairs = seq[(seq.play_type == seq.prev_type) & seq.side.notna() & seq.prev_side.notna()].assign(same=lambda x: (x.side == x.prev_side).astype(int))
    situation = ["team_game", "dn", "dist", "prev_type"]
    for subset, e in (("all", pairs), ("close", pairs[pairs.vegas_wp.between(0.2, 0.8)])):
        res, n = label_test(e, "prev_good", "same", "one", situation + ["prev_side"])
        record("H4", "same side as the last play of that type, after success minus after failure", "main", subset, res, n)
    for kind in ("pass", "run"):
        res, n = label_test(pairs[pairs.play_type == kind], "prev_good", "same", "one", situation + ["prev_side"])
        record("H4", f"same side, {kind} after {kind}", "secondary", "all", res, n)
    res, n = label_test(pairs[pairs.play_type == "pass"], "prev_good", "air_yards", "one", situation)
    record("H4", "air yards of the second pass, after success minus after failure", "secondary", "all", res, n)
    for kind in ("pass", "run"):
        res, n = label_test(seq[seq.prev_type == kind], "prev_good", "same_type", "one", situation)
        record("H4", f"calls a {kind} again after a {kind}, after success minus after failure", "secondary", "all", res, n)

    out = pd.DataFrame(rows)
    (ROOT / "results").mkdir(exist_ok=True)
    out.to_csv(ROOT / "results" / f"{sample}.csv", index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 95)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "explore")
