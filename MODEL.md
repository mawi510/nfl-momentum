# Model: what the feeling of momentum is made of

Fans feel momentum when success follows success and one mistake leads to another. Our four tests in [HYPOTHESES.md](HYPOTHESES.md) found that a play does not change how well the offense plays afterward. This model splits the feeling into three parts that we can measure: the situation a play leaves behind, what the game so far tells us about how good the offense is that day, and whatever is left. The definitions below were set on 2006-2019. Each part then runs once on 2020-2025.

## Part 1: the situation chain

- What it is
  - A table. For each situation, how often the next play succeeds (EPA above zero), is a pass, or is a sack or turnover.
  - A situation is the down, the yards to go (1 to 15, then 16 or more), and one of five field zones.
  - The table uses only the current situation. It is a Markov chain: the past matters only through the situation it left.
  - Built from 2006-2019 plays.
- What we measure on 2020-2025, on plays that follow another play in the same drive
  - The real gap between "after a success" and "after a failure" for each of the three outcomes.
  - The gap that the chain predicts.
  - The share of the real gap that the chain explains, with an interval from resampling games.
- First look on 2006-2019
  - Next play succeeds: 45.3% after a success, 40.0% after a failure. The chain predicts 4.9 of the 5.2 points.
  - Next play is a pass: 50.6% against 72.7%. The chain predicts all of the gap.
  - Next play is a sack or turnover: 4.4% against 7.5%. The chain predicts all of the gap.
  - A failure leaves third or fourth down with 7 or more to go 23% of the time. A success leaves it 1% of the time. In that situation 93% of calls are passes and 12.3% of plays are sacks or turnovers.

## Part 2: belief about the level that day

- What it is
  - Each offense has a level for the game, in EPA above expected per play. The betting line is already removed, so the prior is centered on zero.
  - Prior spread: 0.054. Noise in one play: 1.21. Both from 2006-2019.
  - After n plays, the belief is w times the offense's average so far, with w = n × 0.054² / (n × 0.054² + 1.21²). That is 0.2% after one play and 5.7% after 31 plays.
  - The 95% credible band is the belief plus or minus 1.96 × sqrt(0.054² × 1.21² / (n × 0.054² + 1.21²)).
- Question 1: does the belief forecast the next drive?
  - Unit: each drive from an offense's second drive on, weighted by its number of plays.
  - Outcome: the drive's EPA above expected per play.
  - Measure: the slope of the outcome on the belief at the start of the drive. A slope of 1 means the belief has the correct size.
  - Finding: the 95% interval for the slope on 2020-2025, from resampling games, excludes zero.
  - We also report the gap in outcome between the top and bottom fifth of belief.
- Question 2: what carries the information?
  - Three summaries of the offense's plays so far, each measured against what the chain expects for those situations: the success rate, the rate of gains of 2 or more EPA, and the rate of losses of 2 or more EPA.
  - Measure: one regression of the next-drive outcome on all three, each in standard-deviation units.
  - "Steady success carries it": the success-rate coefficient is positive and its interval excludes zero in both sets of seasons.
  - "Losses tell us more than gains": the size of the loss coefficient minus the size of the gain coefficient has an interval that excludes zero in both sets of seasons.
- Question 3: is the level fixed, or does it move during the game?
  - Measure: add the previous drive's EPA above expected per play to the Question 1 regression.
  - "Recent plays count extra": its coefficient is positive and its interval excludes zero in both sets of seasons.

## Part 3: what is left

- The four tests in [HYPOTHESES.md](HYPOTHESES.md) already measure it: any effect of earlier events after the situation and the level that day are held fixed.
- Result: about 0.01 EPA per play after a missed deep throw, and nothing larger than 0.02 in the other tests.

## What we will show

- One chart that splits the "success follows success" gap into the chain, the level that day, and what is left.
- One game drawn play by play: the belief and its credible band for both offenses.

## Limits

- The 2020-2025 seasons were used once for the four tests. None of the quantities in this file has been computed on them.
- The expected-EPA model already uses the score and the clock. A team that plays well gets a lead and then plays more carefully, which lowers its later numbers. Part 2 therefore measures the information that is left after that effect.
