# Model: what the feeling of momentum is made of

Fans feel momentum when success follows success and one mistake leads to another. Our four tests in [HYPOTHESES.md](HYPOTHESES.md) found that a play does not change how well the offense plays afterward. This model splits the feeling into three parts that we can measure: the situation a play leaves behind, what the game so far tells us about how good the offense is that day, and whatever is left.

## How we train and test

- Every season from 2006 to 2025 is tested once, with everything it needs built from the other 19 seasons.
  - "Everything" is the expected-EPA model, the situation table, and the strength of the prior.
  - Football changed over these years. A situation table built on 2006-2010 predicts a 58.2% pass rate for 2015-2019, and the real rate was 61.7%. Training on seasons from before and after the tested season removes that gap.
- We report three views of the same results.
  - All 20 seasons together.
  - Three eras: 2006-2012, 2013-2019, 2020-2025.
  - 2020-2025 alone. We have not looked at any quantity in this file for those seasons. The first looks below used 2006-2019.
- A result is a finding only if its 95% interval excludes zero for all seasons together and it has the same sign in each of the three eras. Intervals come from resampling whole games.
- The four tests in HYPOTHESES.md keep their own expected-EPA numbers. Nothing here changes them.

## Part 1: the situation chain

- What it is
  - A table. For each situation, how often the next play succeeds (EPA above zero), is a pass, or is a sack or turnover.
  - A situation is the down, the yards to go (1 to 15, then 16 or more), and one of five field zones.
  - The table uses only the current situation. It is a Markov chain: the past matters only through the situation it left.
- What we measure, on plays that follow another play in the same drive
  - The real gap between "after a success" and "after a failure" for each of the three outcomes.
  - The gap that the table predicts.
  - The share of the real gap that the table explains.
- First look on 2006-2019
  - Next play succeeds: 45.3% after a success, 40.0% after a failure. The table predicts 4.9 of the 5.2 points.
  - Next play is a pass: 50.6% against 72.7%. The table predicts all of the gap.
  - Next play is a sack or turnover: 4.4% against 7.5%. The table predicts all of the gap.
  - A failure leaves third or fourth down with 7 or more to go 23% of the time. A success leaves it 1% of the time. In that situation 93% of calls are passes and 12.3% of plays are sacks or turnovers.

## Part 2: belief about the level that day

- The model is Beta-Binomial.
  - What we want to know: the offense's success rate today, compared with what we expected before the game for the situations it faced.
  - The expected rate comes from a model of the situation, the clock, the score, and the betting line. These are the same inputs as expected EPA.
  - Before the game: a Beta prior centered on the expected rate. It counts as a fixed number of plays of evidence. That number comes from how much an offense's first half and second half agree in the other 19 seasons.
  - Each play adds one success or one failure.
  - After any number of plays: belief = (successes minus expected successes) divided by (plays so far plus the prior's plays).
  - The 95% credible band comes from the Beta distribution that the prior and the plays give.
- We compare it with a Normal-Normal model on EPA.
  - Prior: the offense's level in EPA above expected per play is Normal, centered on zero. It counts as about 500 plays.
  - Each play's EPA above expected is treated as Normal around that level. Real plays have more extreme values than a Normal curve, so this is an approximation.
  - Belief = the average so far times plays / (plays + 500).
- First look on 2006-2019
  - Success version, with the prior centered on the table alone: the prior counts as about 390 plays. The model says a first half should move the second-half forecast by 7.4% of the first-half surplus. The data gives 6.2%.
  - EPA version: the model says 5.7%. The data gives 5.0%.
- Question 1: does the belief forecast the next drive?
  - Unit: each drive from an offense's second drive on, weighted by its number of plays.
  - Outcome: the drive's success rate above expected. Second outcome: its EPA above expected per play.
  - We also report the slope for a prior centered on the table alone. That version also learns what the betting line already knew.
  - Measure: the slope of the outcome on the belief at the start of the drive. A slope of 1 means the belief has the correct size.
  - We also report the gap in outcome between the top and bottom fifth of belief.
- Question 2: what carries the information?
  - Three summaries of the offense's plays so far: successes above expected, gains of 2 or more EPA above what the table expects, and losses of 2 or more EPA above what the table expects.
  - Each is divided by (plays so far plus the prior's plays), as the belief is, so that early drives with few plays do not dominate.
  - Measure: one regression of the next drive's EPA above expected per play on all three, each in standard-deviation units.
  - "Steady success carries it": the success-rate coefficient is positive.
  - "Losses tell us more than gains": the size of the loss coefficient is larger than the size of the gain coefficient.
- Question 3: is the level fixed, or does it move during the game?
  - Measure: add the previous drive's success rate above expected to the Question 1 regression.
  - "Recent plays count extra": its coefficient is positive.

## Part 3: what is left

- The four tests in [HYPOTHESES.md](HYPOTHESES.md) already measure it: any effect of earlier events after the situation and the level that day are held fixed.
- Result: about 0.01 EPA per play after a missed deep throw, and nothing larger than 0.02 in the other tests.

## What we will show

- One chart that splits the "success follows success" gap into four parts: the table, what we knew before the game together with the score and clock, the level that day, and what is left.
  - The level that day for a play is the offense's success above expected on its other plays in that game, leaving out the play itself and the play before it.
- One game drawn play by play: the belief and its credible band for both offenses.

## Limits

- The expected-EPA model uses the score and the clock. A team that plays well gets a lead and then plays more carefully, which lowers its later numbers. Part 2 measures the information that is left after that effect.
- The all-seasons view includes 2006-2019, where we took the first looks above. The 2020-2025 view is the clean one.

## Changes before the run

- The success belief first used a prior centered on the table alone. A good offense succeeds more often than the table says from its first play, so that belief would learn during the game what the betting line already knew. The prior is now centered on a rate that includes the betting line. This change was made before any result in this file existed.
