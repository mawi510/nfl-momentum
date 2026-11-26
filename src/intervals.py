"""Second opinion on the four main tests, added after the confirm run.

1. Intervals that resample whole games, to check the shuffle-based intervals.
2. A Bayesian reading: a prior centered on no effect, updated with both sets of seasons.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm

import run_tests as R
from features import ROOT

N_PERM, N_BOOT = 300, 2000
# name, minimum size, direction the hypothesis predicts
TESTS = {"H1": (0.02, -1), "H2": (0.02, 1), "H3": (0.02, 1), "H4": (0.01, 1)}


def per_game(m, masks_fn, lag):
    y, w = m["epa_x"][:, lag:], m["n"][:, lag:]
    return np.stack([np.stack([(y * k).sum(1), (w * k).sum(1)], axis=1) for k in masks_fn(m)], axis=1)


def drive_sums(d, cols, masks_fn, lag=1, seed=0):
    """Per game: the real [sum, count] after each event, and the average over shuffled drive orders."""
    rng = np.random.default_rng(seed)
    d = d.sort_values(["team_game", "pos"])
    games, obs, chance = [], [], []
    for k, g in d.groupby(d.groupby("team_game").pos.transform("size")):
        m = {c: g[c].to_numpy().reshape(-1, k) for c in cols}
        shuffled = np.zeros_like(per_game(m, masks_fn, lag), dtype=float)
        for _ in range(N_PERM):
            order = rng.random(m["n"].shape).argsort(axis=1)
            shuffled += per_game({c: np.take_along_axis(v, order, axis=1) for c, v in m.items()}, masks_fn, lag)
        games.append(g.game_id.to_numpy().reshape(-1, k)[:, 0])
        obs.append(per_game(m, masks_fn, lag))
        chance.append(shuffled / N_PERM)
    return by_game(np.concatenate(games), np.concatenate(obs), np.concatenate(chance))


def by_game(games, obs, chance):
    """Add up the two teams of each game, so a resample keeps a game together."""
    codes, n = pd.factorize(games)[0], len(set(games))
    out = []
    for a in (obs, chance):
        total = np.zeros((n,) + a.shape[1:])
        np.add.at(total, codes, a)
        out.append(total)
    return out


def side_sums(pairs):
    """Per game: real same-side [sum, count] after success and after failure, and what shuffled labels expect."""
    key = pairs[R.SITUATION + ["prev_side"]].astype(str).agg("|".join, axis=1)
    pairs = pairs[pairs.groupby(key).prev_good.transform("nunique") == 2].assign(key=key)
    s = pairs.groupby(["game_id", "key"]).apply(
        lambda g: pd.Series({"s1": g.same[g.prev_good].sum(), "n1": g.prev_good.sum(), "s0": g.same[~g.prev_good].sum(),
                             "n0": (~g.prev_good).sum()}), include_groups=False).reset_index()
    rate = (s.s1 + s.s0) / (s.n1 + s.n0)
    obs = np.stack([s[["s1", "n1"]].to_numpy(float), s[["s0", "n0"]].to_numpy(float)], axis=1)
    chance = np.stack([np.stack([s.n1 * rate, s.n1], axis=1), np.stack([s.n0 * rate, s.n0], axis=1)], axis=1)
    return by_game(s.game_id.to_numpy(), obs, chance)


def resample(obs, chance, contrast, seed=0):
    def effect(o, c):
        return contrast(o[..., 0] / o[..., 1]) - contrast(c[..., 0] / c[..., 1])
    w = np.random.default_rng(seed).multinomial(len(obs), np.ones(len(obs)) / len(obs), size=N_BOOT)
    boots = effect(np.tensordot(w, obs, axes=1), np.tensordot(w, chance, axes=1))
    return effect(obs.sum(0), chance.sum(0)), *np.percentile(boots, [2.5, 97.5]), boots.std()


def game_intervals(sample):
    p, d = R.load(sample)
    cols = ["epa", "epa_x", "n", "deep_tag", "swing_tag"]
    asym = lambda m: -(m[..., 1] + m[..., 2] + m[..., 3] + m[..., 4]) / 2
    out = {
        "H1": resample(*drive_sums(d, cols, R.tag_masks("deep_tag", [1, 2])), lambda m: m[..., 1] - m[..., 2]),
        "H2": resample(*drive_sums(d, cols, R.tag_masks("swing_tag", [1, 2, 3, 4])), asym),
        "H3": resample(*drive_sums(d, cols, R.breakthrough_masks, lag=4), lambda m: m[..., 0]),
        "H4": resample(*side_sums(R.same_side_pairs(p)[1]), lambda m: m[..., 0] - m[..., 1]),
    }
    return pd.DataFrame(out, index=["effect", "low", "high", "se"]).T.assign(sample=sample)


def posterior(est, se, minimum, sign, prior_sd):
    """Normal prior at zero, updated with one estimate per set of seasons."""
    precision = 1 / prior_sd**2 + (1 / se**2).sum()
    mean, sd = (est / se**2).sum() / precision, precision**-0.5
    return {"mean": mean, "low": mean - 1.96 * sd, "high": mean + 1.96 * sd,
            "p_predicted_sign": norm.sf(0, sign * mean, sd),
            "p_predicted_and_above_min": norm.sf(minimum, sign * mean, sd),
            "p_smaller_than_min": norm.cdf(minimum, mean, sd) - norm.cdf(-minimum, mean, sd)}


if __name__ == "__main__":
    games = pd.concat([game_intervals("explore"), game_intervals("confirm")]).rename_axis("hypothesis").reset_index()
    shuffle = pd.concat(pd.read_csv(ROOT / "results" / f"{s}.csv").assign(sample=s) for s in ("explore", "confirm"))
    shuffle = shuffle[(shuffle.role == "main") & (shuffle.subset == "all")][["hypothesis", "sample", "effect", "low", "high"]]
    both = shuffle.merge(games, on=["hypothesis", "sample"], suffixes=("_shuffle", "_games"))
    both["width_ratio"] = (both.high_games - both.low_games) / (both.high_shuffle - both.low_shuffle)
    both.to_csv(ROOT / "results" / "intervals.csv", index=False)
    pd.set_option("display.width", 250)
    print(both.round(4).to_string(index=False))

    rows = []
    for h, (minimum, sign) in TESTS.items():
        g = games[games.hypothesis == h]
        for name, width in (("skeptical", 1.25), ("wide", 5)):
            rows.append({"hypothesis": h, "prior": name, "prior_sd": width * minimum,
                         **posterior(g.effect.to_numpy(), g.se.to_numpy(), minimum, sign, width * minimum)})
    post = pd.DataFrame(rows)
    post.to_csv(ROOT / "results" / "posterior.csv", index=False)
    print(post.round(4).to_string(index=False))
