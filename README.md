# nfl-momentum

Can we find momentum in NFL play-by-play data? This repo is an entry for The Side Quest's [Momentum Lab](https://thesidequest.com/posts/momentum-lab/) challenge.

Our idea is that momentum is mostly something a team loses. A missed big play, a turnover, or a stalled drive should hurt what the offense does next, and hurt it more than a gain of the same size helps. We test four versions of that idea. A clear "no" is a result we will report.

## Status

The tests have run on the explore seasons (2006-2019). See [results/explore.csv](results/explore.csv). The confirm seasons (2020-2025) have not been opened.

## How the tests work

[HYPOTHESES.md](HYPOTHESES.md) has the exact definitions. It was committed before any test touched the 2020-2025 seasons.

- Every outcome is EPA above expected: a play's EPA minus what the down, distance, field position, clock, score, and betting line predict.
- Every test compares events inside one team's game, then repeats the comparison on 2,000 shuffles of that game. The shuffle keeps how good the team was that day and removes only the order.
- We explore on 2006-2019 and confirm once on 2020-2025.

## Run it

```
pip install pandas pyarrow scikit-learn scipy
python src/download.py        # nflverse play-by-play and FTN charting, about 480 MB
python src/prep.py            # one regular-season plays file
python src/features.py        # play and drive tables with EPA above expected
python src/check_shuffle.py   # the shuffle finds nothing in fake games without momentum, and finds a planted effect
python src/replicate.py       # two numbers from the Momentum Lab post, as a check on the data
python src/run_tests.py explore
```

Results are written to `results/`.

## Data

- [nflverse play-by-play](https://github.com/nflverse/nflverse-data/releases/tag/pbp), regular season 2002-2025. The tests use 2006-2025. The earlier seasons are only for the replication check.
- [FTN charting](https://github.com/nflverse/nflverse-data/releases/tag/ftn_charting) through nflverse, 2022-2025.
