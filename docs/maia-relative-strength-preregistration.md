# Maia 2 and Maia 3 relative-strength study: preregistration

## Purpose and scope

This study measures the relative full-game playing strength of selected Maia 2
and Maia 3 engine configurations. It tests whether nominal rating differences
are preserved, compressed, or non-monotonic when the models play one another.

The study does **not** calibrate Maia against a human rating pool. A nominal
`1500` setting must not be interpreted as demonstrated 1500-level human playing
strength. Maia is trained for human move prediction; full-game engine play is a
separate behavioral measurement.

This document is frozen before the 3,000 core games are started. The preceding
timing pilot is operational only and its games are excluded from all reported
strength estimates.

## Pre-registration timing pilot

Before freezing this document, three 40-game pilots used the first 20 opening
prefixes from the suite. The questions and 15-match core schedule had already
been specified. Pilot results were visible when this document was finalized and
are disclosed here; they will not be pooled with, substituted for, or used to
extend any core matchup.

- Maia 2 1100 vs Maia 2 1900: 4 wins, 15 draws, 21 losses for 1100; 28.7%
  score; approximately 68 seconds.
- Maia 3 1100 vs Maia 3 1900: 3 wins, 4 draws, 33 losses for 1100; 12.5%
  score; 1,383.9 seconds.
- Maia 2 1500 vs Maia 3 1500: 11 wins, 13 draws, 16 losses for Maia 2;
  43.8% score; 648.7 seconds.

All 120 games completed. Validated resume accepted every completed PGN without
replaying a game. Each file contained exactly two games for every opening, one
configuration hash, resolved results, and no engine failure or 300-ply cutoff.

The measured rates project approximately 14.6 engine-hours for the core study.
The operational budget is conservatively set to 15–18 hours because adjacent
ratings may produce longer and more drawish games than the pilot workloads.
Maia 2 writes two harmless model-loading messages before normal UCI output, and
Maia 3 checks checkpoint resolution at startup even when its model is cached;
both behaviors will be recorded but are not exclusion conditions.

## Primary questions

1. Is playing strength monotonic across nominal ratings within each generation?
2. How much of each nominal 200-point and 800-point separation is realized?
3. Does Maia 3 preserve more rating separation than Maia 2?
4. At equal nominal ratings, does the relative Maia 2/Maia 3 advantage change
   from the bottom to the top of the tested range?
5. Which adjacent interval is each generation's best-preserved relative-rating
   region?

## Frozen engine configurations

Ratings are `1100`, `1300`, `1500`, `1700`, and `1900`.

Maia 2 uses the installed Maia 2 rapid model through its UCI wrapper. Every
engine instance receives separate `SelfElo` and `OppoElo` values. Maia 3 uses
the 79M checkpoint on CPU with `Temperature=0`, `TopP=1`, separate self and
opponent ratings, and UCI history enabled. Both families use one requested node
per move. No opening books are enabled.

The exact benchmark, wrapper, model checkpoint, Python dependency, operating
system, and hardware identifiers will be recorded in the final report. Any
post-registration change required to complete the study will be disclosed with
its reason and affected games.

## Match schedule

Within Maia 2 and separately within Maia 3:

- 1100 vs 1300
- 1300 vs 1500
- 1500 vs 1700
- 1700 vs 1900
- 1100 vs 1900

Across generations:

- Maia 2 1100 vs Maia 3 1100
- Maia 2 1300 vs Maia 3 1300
- Maia 2 1500 vs Maia 3 1500
- Maia 2 1700 vs Maia 3 1700
- Maia 2 1900 vs Maia 3 1900

There are 15 matchups and 200 games per matchup, for 3,000 core games.

## Opening control

All matchups use
[`openings/maia-relative-strength-100.pgn`](../openings/maia-relative-strength-100.pgn).
Each of its 100 prefixes is played twice, with engine colors reversed. The
suite is frozen at SHA-256
`3ad5d17fcd30bac36ef7277b15232e7df27bdb0728faa9ab441503d826cbc171`.

The suite was derived without reference to game outcomes from the public
1,000-game Maia 1600 benchmark. For every source game, only its first eight
plies were considered. Positions were retained only when they were legal,
nonterminal, not in check, materially equal, and unique by position. Selection
was deterministic using the seed `maia-relative-strength-v1`, with initial
coverage targets for e4, d4, Nf3, and c4. Available source diversity produced
51 e4, 30 d4, 10 c4, 7 Nf3, and 2 other prefixes.

This is a common opening control, not a claim that the suite represents the
distribution of human openings at any particular rating.

## Run and integrity rules

- Match order may be arranged for operational efficiency, but no matchup may be
  added, removed, or extended based on interim results.
- Engine A is the first-listed profile; every opening is color-reversed by the
  benchmark tool.
- Maximum game length is 300 plies. Games reaching the limit are draws.
- Completed games are flushed after every game. Interrupted matches use the
  benchmark's validated `--resume` mode.
- A game is excluded only if it is missing, has an unresolved result, violates
  the frozen opening prefix/color schedule, has a configuration-hash mismatch,
  or reflects a documented engine/tool failure.
- A failed game will be rerun under the identical configuration. Both the
  failure and replacement will be disclosed; the failed game will not enter
  strength estimates.
- Pilot games and all development smoke tests are excluded.

## Frozen outcomes and statistical analysis

For each matchup, report wins, draws, losses, score percentage, color split,
termination distribution, and the higher-rated or first-listed profile's score.

For score `p`, descriptive realized Elo is
`400 * log10(p / (1 - p))`. Infinite endpoint estimates are reported as bounds
rather than silently clipped. The compression ratio for a within-family match
is realized Elo difference divided by nominal Elo difference.

Uncertainty is calculated by resampling the 100 opening pairs as clusters, so
the two color-reversed games from one prefix remain together. Report percentile
95% cluster-bootstrap intervals using a fixed published seed and at least
10,000 replicates. A result is directionally resolved when its interval excludes
50% score. Family-level latent ratings are fitted on the complete connected
match graph using a Bradley-Terry model with draws contributing half a point;
the final report will include model diagnostics and a sensitivity analysis
using a draw-aware Davidson formulation if stable.

For each family, regress fitted relative playing strength on nominal rating.
The slope is the global scale-preservation estimate: 1 suggests preservation,
between 0 and 1 compression, approximately 0 little separation, and below 0 a
reversal. Compare the Maia 2 and Maia 3 slopes with a pair-cluster bootstrap.

The primary family-level comparisons are the two slopes, their difference, and
the two 1100-vs-1900 endpoint gaps. Adjacent intervals and the five equal-label
cross-generation matches are secondary. Raw intervals are always reported;
Holm-adjusted p-values will accompany the family of five cross-generation
tests and each family of four adjacent-band tests.

## Interpretation rules

- "Compression" means realized engine-relative separation below the nominal
  separation; it does not establish human-rating miscalibration.
- Maia 3 has improved dynamic range only if its fitted slope or endpoint gap is
  credibly larger, not merely because it is uniformly stronger.
- A lower Maia 3 setting being weaker while a higher setting is stronger than
  Maia 2 is evidence of expanded relative range.
- A "best-preserved relative-rating region" is the adjacent interval whose
  realized gap is closest to 200 while remaining monotonic. It will not be
  called an accurate human-Elo sweet spot.
- Exploratory observations, including opening-specific effects and unusual
  termination patterns, will be labeled exploratory.

## Planned publication

The final report will include methodology, results, limitations, performance
observations, all matchup PGNs, a game-level table, derived statistical tables,
the frozen suite and configuration hashes, analysis code or exact formulas,
and file checksums. Private orchestration used to invoke the public two-engine
tool is not part of the benchmark product and will not be published.
