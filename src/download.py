"""Download nflverse play-by-play and FTN charting files into data/raw/."""

import pathlib
import urllib.request

RELEASES = "https://github.com/nflverse/nflverse-data/releases/download"
PBP_SEASONS = range(2002, 2026)  # 2002-2005 only for checks against the post
FTN_SEASONS = range(2022, 2026)
RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"


def fetch(url, dest):
    if dest.exists():
        return
    print("downloading", dest.name)
    urllib.request.urlretrieve(url, dest)


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    for year in PBP_SEASONS:
        name = f"play_by_play_{year}.parquet"
        fetch(f"{RELEASES}/pbp/{name}", RAW / name)
    for year in FTN_SEASONS:
        name = f"ftn_charting_{year}.parquet"
        fetch(f"{RELEASES}/ftn_charting/{name}", RAW / name)
