"""Chance tests: shuffle drive order, or shuffle event labels, inside each team's game."""

import numpy as np


def order_shuffle(drives, cols, stat_fn, n_perm=2000, seed=0):
    """Shuffle the order of each team's drives within a game.

    stat_fn gets {column: matrix of team-games x drives} and returns an array of
    [sum, count] rows. Returns the observed means, the means for each shuffle, and the counts.
    """
    rng = np.random.default_rng(seed)
    drives = drives.sort_values(["team_game", "pos"])
    length = drives.groupby("team_game").pos.transform("size")
    groups = [
        {c: g[c].to_numpy().reshape(-1, k) for c in cols} for k, g in drives.groupby(length)
    ]
    obs = sum(stat_fn(m) for m in groups)
    perm = np.zeros((n_perm,) + obs.shape)
    for i in range(n_perm):
        for m in groups:
            order = rng.random(m[cols[0]].shape).argsort(axis=1)
            perm[i] += stat_fn({c: np.take_along_axis(v, order, axis=1) for c, v in m.items()})
    return obs[:, 0] / obs[:, 1], perm[:, :, 0] / perm[:, :, 1], obs[:, 1]


def label_shuffle(group, label, n_perm=2000, seed=0):
    """Yield the labels shuffled among the events that share a group."""
    rng = np.random.default_rng(seed)
    order = np.argsort(group, kind="stable")
    g, lab = np.asarray(group)[order], np.asarray(label)[order]
    for _ in range(n_perm):
        out = np.empty_like(lab)
        out[order] = lab[np.lexsort((rng.random(len(g)), g))]
        yield out


def summarize(obs, perm):
    """Effect above chance, a 95% interval from the shuffle spread, and a two-sided p-value."""
    effect = obs - perm.mean()
    half = 1.96 * perm.std()
    p = (1 + np.sum(np.abs(perm - perm.mean()) >= abs(effect))) / (1 + len(perm))
    return {"observed": obs, "chance": perm.mean(), "effect": effect,
            "low": effect - half, "high": effect + half, "p": p}
