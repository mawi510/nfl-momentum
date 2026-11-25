"""Build the play and drive tables every test reads, with EPA above expected."""

import pathlib

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPLORE = range(2006, 2020)
CONFIRM = range(2020, 2026)

# What the situation and the two teams predict for a play's EPA.
CONTROLS = [
    "down", "ydstogo", "yardline_100", "half_seconds_remaining",
    "game_seconds_remaining", "score_differential", "implied_pts", "exp_margin",
]


def load_plays():
    p = pd.read_parquet(ROOT / "data" / "plays.parquet")
    p = p[p.season >= EXPLORE[0]]
    p = p[p.play_type.isin(["run", "pass"]) & p.epa.notna() & p.down.notna()].copy()
    home = p.posteam == p.home_team
    p["exp_margin"] = np.where(home, p.spread_line, -p.spread_line)
    p["implied_pts"] = p.total_line / 2 + p.exp_margin / 2
    p["team_game"] = p.game_id + "_" + p.posteam
    p["good"] = (p.epa > 0).astype(int)
    p["att"] = p.air_yards.notna().astype(int)
    p["deep"] = (p.air_yards >= 20).astype(int)
    margin = np.where(home, p.result, -p.result)
    p["won"] = (margin > 0) + 0.5 * (margin == 0)

    # Fit on explore seasons only, so the confirm seasons stay unseen.
    fit = p[p.season.isin(EXPLORE)]
    model = HistGradientBoostingRegressor(
        max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=200,
        early_stopping=False, random_state=0,
    )
    model.fit(fit[CONTROLS], fit.epa)
    p["epa_x"] = p.epa - model.predict(p[CONTROLS])
    return p.reset_index(drop=True)


def build_drives(p):
    d = (
        p.groupby(["season", "game_id", "posteam", "team_game", "fixed_drive"], sort=False)
        .agg(
            n=("epa", "size"), epa=("epa", "sum"), epa_x=("epa_x", "sum"),
            start_wp=("vegas_wp", "first"), max_epa=("epa", "max"), min_epa=("epa", "min"),
            won=("won", "first"), first_pass=("pass", "first"),
            qtr=("qtr", "first"), att=("att", "sum"), deep=("deep", "sum"),
        )
        .reset_index()
        .sort_values(["season", "game_id", "posteam", "fixed_drive"], ignore_index=True)
    )
    d["pos"] = d.groupby("team_game").cumcount()
    d["close"] = d.start_wp.between(0.2, 0.8)
    d["win_x"] = d.won - d.start_wp
    d["one"] = 1
    return d


if __name__ == "__main__":
    plays = load_plays()
    plays.to_parquet(ROOT / "data" / "plays_x.parquet")
    build_drives(plays).to_parquet(ROOT / "data" / "drives.parquet")

    # Rubber band check: raw EPA should rise for trailing teams, EPA above expected should not.
    ex = plays[plays.season.isin(EXPLORE) & (plays.qtr >= 3)]
    bins = pd.cut(ex.score_differential, [-60, -17, -9, -1, 0, 8, 16, 60])
    print(ex.groupby(bins, observed=True)[["epa", "epa_x"]].mean().round(3))
