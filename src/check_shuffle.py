"""Check the shuffle on simulated games: it must find nothing without momentum and find a planted effect."""

import numpy as np
import pandas as pd

from shuffle import order_shuffle, summarize


def simulate(carry, n_games=3000, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(n_games):
        quality = rng.normal(0, 0.5)  # how good this team is in this game
        prev_good = False
        for pos in range(rng.integers(9, 14)):
            epa = rng.normal(quality + (carry if prev_good else 0), 2)
            rows.append((f"g{g}", pos, epa))
            prev_good = epa > 0
    return pd.DataFrame(rows, columns=["team_game", "pos", "epa"])


def after_good_minus_after_bad(m):
    prev_good, nxt = m["epa"][:, :-1] > 0, m["epa"][:, 1:]
    return np.array([[nxt[prev_good].sum(), prev_good.sum()], [nxt[~prev_good].sum(), (~prev_good).sum()]])


if __name__ == "__main__":
    for name, carry in (("no momentum", 0.0), ("planted carry-over of 0.3 EPA", 0.3)):
        obs, perm, _ = order_shuffle(simulate(carry), ["epa"], after_good_minus_after_bad, n_perm=500)
        res = summarize(obs[0] - obs[1], perm[:, 0] - perm[:, 1])
        print(f"{name}: raw gap {res['observed']:.3f}, chance {res['chance']:.3f}, "
              f"effect {res['effect']:.3f} [{res['low']:.3f}, {res['high']:.3f}], p {res['p']:.3f}")
