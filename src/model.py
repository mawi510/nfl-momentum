"""Step 2 of MODEL.md: measure the three parts on data/plays_cv.parquet and write results/model.csv."""

import numpy as np
import pandas as pd

from features import ROOT

N_BOOT = 2000
VIEWS = {"all seasons": (2006, 2025), "2006-2012": (2006, 2012), "2013-2019": (2013, 2019), "2020-2025": (2020, 2025)}
rows = []


def record(part, measure, view, est, low, high):
    rows.append({"part": part, "measure": measure, "view": view, "estimate": est, "low": low, "high": high})


def resample(per_game, fn, seed=0):
    """Estimate fn(column sums), with a 95% interval from resampling whole games."""
    a = per_game.to_numpy(float)
    w = np.random.default_rng(seed).multinomial(len(a), np.ones(len(a)) / len(a), size=N_BOOT)
    boots = np.array([fn(row) for row in w @ a])
    return np.column_stack([fn(a.sum(0)), np.percentile(boots, 2.5, axis=0), np.percentile(boots, 97.5, axis=0)])


def regression(d, y, xs, extra=None):
    """Weighted least squares of y on xs with an intercept, drives weighted by plays, games resampled.

    Returns one [estimate, low, high] row per x, then one per function in extra.
    """
    X = np.column_stack([np.ones(len(d))] + [d[x].to_numpy(float) for x in xs])
    k, w = X.shape[1], d.n.to_numpy(float)
    parts = np.column_stack([(w[:, None, None] * X[:, :, None] * X[:, None, :]).reshape(len(d), -1), w[:, None] * X * d[y].to_numpy(float)[:, None]])
    per_game = pd.DataFrame(parts).groupby(d.game_id.to_numpy()).sum()

    def fn(s):
        beta = np.linalg.solve(s[: k * k].reshape(k, k), s[k * k:])[1:]
        return np.concatenate([beta, [f(beta) for f in (extra or [])]])

    return resample(per_game, fn)


def chain_part(p, view):
    seq = p[p.prev_good.notna()]
    after = seq.prev_good.to_numpy() == 1
    for name, col in (("next play succeeds", "good"), ("next play is a pass", "pass"), ("next play is a sack or turnover", "mistake")):
        cols = {"y1": seq[col] * after, "t1": seq[f"tab_{col}"] * after, "n1": after, "y0": seq[col] * ~after, "t0": seq[f"tab_{col}"] * ~after, "n0": ~after}
        per_game = pd.DataFrame(cols).groupby(seq.game_id.to_numpy()).sum()

        def fn(s):
            real, table = s[0] / s[2] - s[3] / s[5], s[1] / s[2] - s[4] / s[5]
            return np.array([100 * real, 100 * table, 100 * table / real])

        out = resample(per_game, fn)
        for label, r in zip(("real gap, points", "gap the table predicts, points", "share explained, %"), out):
            record("1 chain", f"{name}: {label}", view, *r)

    # Split the success gap into four parts for the chart.
    cols = {}
    for flag, tag in ((after, "1"), (~after, "0")):
        for c in ("good", "tab_good", "exp_good", "level"):
            cols[c + tag] = seq[c] * flag
        cols["n" + tag] = flag
    per_game = pd.DataFrame(cols).groupby(seq.game_id.to_numpy()).sum()

    def fn(s):
        gap = 100 * (s[0:4] / s[4] - s[5:9] / s[9])  # real, table, expected, level
        return np.array([gap[1], gap[2] - gap[1], gap[3], gap[0] - gap[2] - gap[3]])

    for label, r in zip(("table", "before the game, score and clock", "level that day", "left over"), resample(per_game, fn)):
        record("1 chain", f"success gap split, points: {label}", view, *r)


def belief_part(d, view):
    d = d[d.plays_before > 0].copy()
    # Question 1
    for name, y, x in (("success belief on success above expected (main)", "y_good", "b_good"),
                       ("table-centered belief on success above the table", "y_tab", "b_tab"),
                       ("EPA belief on EPA above expected", "y_epa", "b_epa"),
                       ("success belief on EPA above expected", "y_epa", "b_good")):
        record("2 Q1 forecast", f"slope: {name}", view, *regression(d, y, [x])[0])
    cuts = d.b_good.quantile([0.2, 0.8]).to_numpy()
    top, bottom = (d.b_good >= cuts[1]).to_numpy(), (d.b_good <= cuts[0]).to_numpy()
    for label, y, scale in (("success rate, points", "y_good", 100), ("EPA per play", "y_epa", 1)):
        cols = {"yt": d[y] * d.n * top, "nt": d.n * top, "yb": d[y] * d.n * bottom, "nb": d.n * bottom}
        per_game = pd.DataFrame(cols).groupby(d.game_id.to_numpy()).sum()
        record("2 Q1 forecast", f"top fifth of belief minus bottom fifth: {label}", view,
               *resample(per_game, lambda s: np.array([scale * (s[0] / s[1] - s[2] / s[3])]))[0])

    # Question 2
    z = d[["s_good", "s_gain", "s_loss"]].apply(lambda c: (c - np.average(c, weights=d.n)) / np.sqrt(np.cov(c, aweights=d.n)))
    out = regression(d.assign(**z), "y_epa", ["s_good", "s_gain", "s_loss"], extra=[lambda b: -b[2] - b[1]])
    for label, r in zip(("steady success", "big gains", "big losses", "size of loss minus size of gain"), out):
        record("2 Q2 what carries it", f"EPA per play for one standard deviation: {label}", view, *r)

    # Question 3
    e = d[d.prev_rate.notna()]
    out = regression(e, "y_good", ["b_good", "prev_rate"])
    record("2 Q3 recent plays", "slope on the belief", view, *out[0])
    record("2 Q3 recent plays", "extra slope on the previous drive", view, *out[1])


if __name__ == "__main__":
    p = pd.read_parquet(ROOT / "data" / "plays_cv.parquet").sort_values(["team_game", "fixed_drive", "play_id"], ignore_index=True)
    print("prior counts as this many plays (range over seasons):",
          {c: (int(p[c].min()), int(p[c].max())) for c in ("n_good", "n_tab", "n_epa")})
    p["prev_good"] = p.groupby(["team_game", "fixed_drive"]).good.shift(1)
    # Level that day: success above expected on the offense's other drives in the game. Plays in the
    # same drive are left out because a drive ends on a failure, which ties its plays together.
    surplus = p.good - p.exp_good
    game, drive = surplus.groupby(p.team_game), surplus.groupby([p.team_game, p.fixed_drive])
    p["level"] = (game.transform("sum") - drive.transform("sum")) / (game.transform("size") - drive.transform("size"))

    sums = {"n": ("good", "size"), "S": ("good", "sum"), "E": ("exp_good", "sum"), "T": ("tab_good", "sum"), "X": ("epa_x", "sum"),
            "G": ("gain", "sum"), "Gt": ("tab_gain", "sum"), "L": ("loss", "sum"), "Lt": ("tab_loss", "sum")}
    d = p.groupby(["season", "game_id", "team_game", "fixed_drive"], sort=False).agg(
        **sums, n_good=("n_good", "first"), n_tab=("n_tab", "first"), n_epa=("n_epa", "first")).reset_index()
    d = d.sort_values(["team_game", "fixed_drive"], ignore_index=True)
    before = d.groupby("team_game")[list(sums)].cumsum() - d[list(sums)]
    d["plays_before"] = before.n
    d["b_good"] = (before.S - before.E) / (before.n + d.n_good)
    d["b_tab"] = (before.S - before["T"]) / (before.n + d.n_tab)
    d["b_epa"] = before.X / (before.n + d.n_epa)
    d["s_good"], d["s_gain"], d["s_loss"] = d.b_good, (before.G - before.Gt) / (before.n + d.n_good), (before.L - before.Lt) / (before.n + d.n_good)
    d["y_good"], d["y_tab"], d["y_epa"] = (d.S - d.E) / d.n, (d["S"] - d["T"]) / d.n, d.X / d.n
    d["prev_rate"] = d.groupby("team_game").y_good.shift(1)

    for view, (lo, hi) in VIEWS.items():
        chain_part(p[p.season.between(lo, hi)], view)
        belief_part(d[d.season.between(lo, hi)], view)

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results" / "model.csv", index=False)
    d.to_parquet(ROOT / "data" / "drives_cv.parquet")
    wide = out.assign(cell=out.apply(lambda r: f"{r.estimate:.3f} [{r.low:.3f}, {r.high:.3f}]", axis=1)).pivot(index=["part", "measure"], columns="view", values="cell")
    pd.set_option("display.width", 260, "display.max_colwidth", 80, "display.max_rows", 200)
    print(wide[list(VIEWS)].to_string())
