"""Step 1 of MODEL.md: for each season, build everything from the other 19 seasons and apply it.

Writes data/plays_cv.parquet. Every number in it for a season comes from models, tables, and
prior strengths that never saw that season.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

from features import CONTROLS, ROOT

STATE = ["down", "dist", "zone"]
OUTCOMES = ["good", "pass", "mistake", "gain", "loss"]
PARAMS = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=200, early_stopping=False, random_state=0)
KEEP = ["season", "game_id", "team_game", "posteam", "defteam", "fixed_drive", "play_id", "qtr", "epa", "desc"] + CONTROLS


def load():
    p = pd.read_parquet(ROOT / "data" / "plays_x.parquet")
    p = p.sort_values(["season", "game_id", "play_id"], ignore_index=True)
    out = p[KEEP].copy()
    out["good"] = p.good
    out["pass"] = p["pass"].astype(int)
    out["mistake"] = ((p.sack == 1) | (p.interception == 1) | (p.fumble_lost == 1)).astype(int)
    out["gain"], out["loss"] = (p.epa >= 2).astype(int), (p.epa <= -2).astype(int)
    out["dist"] = p.ydstogo.clip(upper=16)
    out["zone"] = pd.cut(p.yardline_100, [0, 10, 20, 50, 80, 100]).astype(str)
    return out


def prior_plays(train, surplus, noise):
    """How many plays the prior counts as: play noise divided by how much a team's two halves agree."""
    t = train[train.qtr <= 4].assign(x=surplus, half=lambda d: np.where(d.qtr <= 2, 1, 2))
    halves = t.groupby(["team_game", "half"]).x.mean().unstack().dropna()
    return noise / np.cov(halves[1], halves[2])[0, 1]


def fold(p, season):
    train, test = p[p.season != season].copy(), p[p.season == season].copy()
    epa_model = HistGradientBoostingRegressor(**PARAMS).fit(train[CONTROLS], train.epa)
    good_model = HistGradientBoostingClassifier(**PARAMS).fit(train[CONTROLS], train.good)
    table = train.groupby(STATE)[OUTCOMES].mean().add_prefix("tab_")
    for frame in (train, test):
        frame["epa_x"] = frame.epa - epa_model.predict(frame[CONTROLS])
        frame["exp_good"] = good_model.predict_proba(frame[CONTROLS])[:, 1]
        tab = frame[STATE].join(table, on=STATE)[table.columns].fillna(train[OUTCOMES].mean().add_prefix("tab_"))
        frame[table.columns] = tab.to_numpy()
    # Prior strength for: success above expected, success above the table, and EPA above expected.
    test["n_good"] = prior_plays(train, train.good - train.exp_good, (train.exp_good * (1 - train.exp_good)).mean())
    test["n_tab"] = prior_plays(train, train.good - train.tab_good, (train.tab_good * (1 - train.tab_good)).mean())
    test["n_epa"] = prior_plays(train, train.epa_x, train.epa_x.var())
    print(season, test[["n_good", "n_tab", "n_epa"]].iloc[0].round(0).to_dict(), flush=True)
    return test


if __name__ == "__main__":
    p = load()
    pd.concat([fold(p, s) for s in sorted(p.season.unique())]).to_parquet(ROOT / "data" / "plays_cv.parquet")
    print("done", flush=True)
