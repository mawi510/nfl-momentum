"""Size "momentum as information": how much do a team's earlier plays in a game tell us about its later plays?

Exploratory, 2006-2019 only. Every number is EPA above expected, so what the betting line knew before
the game is already removed.
"""

import numpy as np
import pandas as pd

from features import EXPLORE, ROOT


def ols(y, X):
    """Coefficients and standard errors, with an intercept added."""
    X = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    cov = np.linalg.inv(X.T @ X) * resid.var(ddof=X.shape[1])
    return beta[1:], np.sqrt(np.diag(cov))[1:]


if __name__ == "__main__":
    p = pd.read_parquet(ROOT / "data" / "plays_x.parquet")
    p = p[p.season.isin(EXPLORE) & (p.qtr <= 4)]

    # 1. Do a team's quarters move together? A fixed "level that day" gives the same covariance for every
    #    pair of quarters. A level that drifts gives more for quarters next to each other.
    q = p.groupby(["team_game", "qtr"]).epa_x.mean().unstack().dropna()
    cov = q.cov()
    print("covariance of a team's quarter averages (x1000), and its standard error:")
    for a in range(1, 5):
        for b in range(a + 1, 5):
            prod = (q[a] - q[a].mean()) * (q[b] - q[b].mean())
            print(f"  Q{a}-Q{b}: {1000 * cov.loc[a, b]:6.2f} +/- {1000 * prod.std() / np.sqrt(len(q)):.2f}")
    near = np.mean([cov.loc[1, 2], cov.loc[2, 3], cov.loc[3, 4]])
    far = np.mean([cov.loc[1, 3], cov.loc[2, 4], cov.loc[1, 4]])
    tau2, sigma2 = np.mean([near, far]), p.epa_x.var()
    print(f"neighbors {1000 * near:.2f}, apart {1000 * far:.2f} | spread of the level that day: sd {np.sqrt(tau2):.3f} EPA per play | one play: sd {np.sqrt(sigma2):.2f}")

    # 2. How far should n plays move our forecast? weight = share of the average so far that we believe.
    print("weight on the game so far after n plays:", {n: round(n * tau2 / (n * tau2 + sigma2), 3) for n in (5, 10, 20, 31, 45, 60)})

    # 3. Check it: first-half average against second-half average.
    half = p.assign(h=np.where(p.qtr <= 2, 1, 2)).groupby(["team_game", "h"]).agg(x=("epa_x", "mean"), n=("epa_x", "size"), good=("good", "mean")).unstack()
    half = half.dropna()
    first, second = half.x[1], half.x[2]
    slope, se = ols(second.to_numpy(), first.to_numpy())
    print(f"plays in a first half: {half.n[1].mean():.0f} | second half moves {slope[0]:.3f} +/- {se[0]:.3f} per 1.0 of first half")
    bins = pd.qcut(first, 5, labels=["worst fifth", "2", "3", "4", "best fifth"])
    print(pd.DataFrame({"first half": first.groupby(bins, observed=True).mean(), "second half": second.groupby(bins, observed=True).mean()}).round(3).T.to_string())

    # 4. Steady success or big plays: which part of the first half carries the information?
    z = lambda s: ((s - s.mean()) / s.std()).to_numpy()
    for name, X in (("average EPA alone", [z(first)]), ("success rate alone", [z(half.good[1])]), ("both together", [z(first), z(half.good[1])])):
        b, s = ols(second.to_numpy(), np.column_stack(X))
        print(f"  {name}: " + ", ".join(f"{bi:.4f} +/- {si:.4f}" for bi, si in zip(b, s)))
