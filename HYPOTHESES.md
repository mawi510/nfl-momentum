# Hypotheses and tests

This file was committed before any test touched the 2020-2025 seasons. The definitions were set on 2006-2019 only. The last section lists what we changed after the first run on those seasons, and why.

## The question

Momentum exists if an earlier event in a game changes how a team plays or decides later in that same game, after we account for the situation, the two teams, the score, and chance. Our working idea is that momentum is mostly something a team loses through failed execution, and that a loss changes later play more than a gain of the same size.

## Data and split

- nflverse play-by-play, regular season. A play is a run or pass with a down and an EPA value.
- Explore seasons: 2006-2019. We can look at these as often as we like.
- Confirm seasons: 2020-2025. Each main test runs on these once.
- FTN charting (drops and catchable balls) exists for 2022-2025 only, so it is a second check in the confirm seasons.

## Controls

- **Situation, teams, and score.** A model predicts each play's EPA from down, distance, field position, clock, score margin, and the betting market's view of the two teams (expected margin and expected points for the offense). The model is fit on 2006-2019 only. Every outcome below is "EPA above expected": the play's EPA minus this prediction.
- **How good the team was that day, and chance.** Each test compares events inside one team's game, then repeats the comparison 2,000 times on shuffled data. Drive tests (H1 to H3) shuffle the order of the team's drives in that game. The play test (H4) shuffles the success labels among that team's plays in the same situation. The effect is the real result minus the average shuffled result.
- **Rubber band.** Each main test is repeated on close games only: the outcome drive starts with a win probability between 20% and 80%.
- **End of game.** A long, good drive is more often a team's last drive, so the last drive is not a typical drive. Each drive test is repeated with every team's last drive removed.

## Main tests

One main test per hypothesis. The outcome for H1 to H3 is EPA above expected per play on the offense's next drive.

- **H1, missed opportunity**
  - Events: deep targets, 20 or more air yards, completion probability 0.25 or more, not intercepted.
  - Drive groups: drives with only incomplete deep targets (missed) and drives with only complete ones (made).
  - Statistic: next-drive outcome after a missed drive minus next-drive outcome after a made drive.
  - Chance test: shuffle the order of the team's drives in that game.
  - Momentum predicts a negative value.
- **H2, loss against gain**
  - Events: drives whose largest play by EPA size is 2 or more. Size bins are 2 to 3 and 3 or more. A drive with both a gain and a loss of 2 or more is not an event.
  - Statistic: the drop after a loss minus the rise after a gain, each measured against chance, averaged over the two size bins.
  - Chance test: shuffle the order of the team's drives in that game.
  - Our idea predicts a positive value. We report the loss effect and the gain effect separately too.
- **H3, breakthrough after struggle**
  - Event: three or more drives in a row with total EPA below zero, then a drive with total EPA above zero.
  - Statistic: outcome on the drive after the good drive.
  - Chance test: shuffle the order of the team's drives in that game.
  - Momentum predicts a positive value.
- **H4, where the ball goes**
  - Events: two plays in a row in one drive that are both passes or both runs, each with a recorded side (left, middle, right).
  - Labels: the first play had EPA above zero (success) or not.
  - Statistic: how often the second play goes to the same side after a success, minus the same rate after a failure.
  - Chance test: shuffle the labels among pairs that share the team's game, the play type, the side of the first play, and the down and distance group (1 to 3, 4 to 7, 8 or more yards) of the second play.
  - "Go back to what worked" predicts a positive value.

## What counts as a finding

A main test is a finding only if it does all four:

1. Beats the shuffle at p < 0.0125 in the explore seasons (0.05 divided across four tests).
2. Has the same sign in the confirm seasons, with a 95% interval that excludes zero.
3. Is at least 0.02 EPA per play for H1 to H3, or 1 percentage point for H4.
4. Has the same sign in close games and, for H1 to H3, with each team's last drive removed.

Other outcomes:

- **No effect.** The confirm interval sits fully inside the minimum size in rule 3. We report "no effect larger than X".
- **Not enough data.** The confirm interval includes both zero and values beyond the minimum size.

The 95% interval is the effect plus or minus 1.96 times the standard deviation of the shuffled results.

## Secondary tests

These are reported in full but cannot become findings on their own.

- H1: missed and made drives each compared with chance. The share of next-drive passes that are deep, after a missed drive minus after a made drive. Drives with a gain of 20 or more yards erased by an offensive penalty against drives with a gain of 20 or more that stood. In 2022-2025, drives with an FTN drop or uncaught catchable deep ball against drives with a caught deep ball.
- H2: the loss effect and the gain effect, each against chance. Whether the first play of the next drive is a pass, after a loss minus after a gain.
- H3: whether the team wins more often than its win probability at the start of the next drive says, measured against the same gap over all drives, with games as the unit. The drive after a breakthrough against the drive after an ordinary good drive. The drive after four or more bad drives in a row.
- H4: same side for passes and runs separately. Depth of the second pass after a successful pass. How often a team calls the same play type again after a success.

We report every test we run, including the ones that find nothing.

## Changes after the first explore run

All three changes were made on 2006-2019 data, before any confirm run.

- **H1 moved from a label shuffle to the drive shuffle.** The first version shuffled "caught" and "missed" among a team's deep throws and compared their next drives. It showed the next drive was 0.043 EPA per play better after a miss, which is a bias in the test. The next drive after a miss can itself contain a caught deep throw, and a team's game with one of each always pairs them that way. Miller and Sanjurjo describe the same bias in the hot-hand studies. The drive shuffle moves each drive with its own events, so it does not have this bias.
- **H4 strata now include distance and the first play's side.** A success changes the distance to go, and the distance changes the call. With distance in the strata the first result (0.9 points more often to the same side) went to zero.
- **A check with the last drive removed was added.** The last drive of a team's game is 0.066 EPA per play above expected, because a long, good drive runs out the clock. Events that happen late in games are followed by that drive more often than the shuffle expects.
