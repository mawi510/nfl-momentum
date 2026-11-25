"""Stack regular-season play-by-play into data/plays.parquet with only the columns we use."""

import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

COLUMNS = [
    "game_id", "play_id", "season", "season_type", "week", "home_team", "away_team",
    "posteam", "defteam", "qtr", "down", "ydstogo", "yardline_100",
    "game_seconds_remaining", "half_seconds_remaining", "score_differential",
    "spread_line", "total_line", "result", "play_type", "pass", "rush", "qb_dropback", "qb_spike", "qb_kneel",
    "epa", "ep", "wp", "vegas_wp", "wpa", "success", "yards_gained", "first_down",
    "touchdown", "td_team", "cp", "cpoe", "air_yards", "air_epa", "yac_epa", "xyac_epa",
    "complete_pass", "incomplete_pass", "interception", "fumble_lost", "sack",
    "penalty", "penalty_team", "penalty_yards", "pass_location", "pass_length",
    "run_location", "run_gap", "fixed_drive", "fixed_drive_result", "series",
    "series_success", "order_sequence", "desc",
]

if __name__ == "__main__":
    frames = []
    for path in sorted(RAW.glob("play_by_play_*.parquet")):
        df = pd.read_parquet(path, columns=COLUMNS)
        frames.append(df[df.season_type == "REG"])
    plays = pd.concat(frames, ignore_index=True)
    plays = plays.sort_values(["season", "week", "game_id", "play_id"], ignore_index=True)
    plays.to_parquet(ROOT / "data" / "plays.parquet")
    print(plays.groupby("season").game_id.nunique().to_dict())
    print(len(plays), "rows")
