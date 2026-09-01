# Supplemental Appendix: Maia 3 High-Rating Compression

This preregistered follow-up extends the
[Maia 2 and Maia 3 relative-strength study](../../README.md) beyond its
1100–1900 range. It measures two additional Maia 3 matchups—1600 vs 2100 and
1600 vs 2300—using the same frozen 100-opening suite, deterministic one-node
play, paired colors, model checkpoint, and analysis framework.

This appendix adds high-label evidence; it does not revise or pool the original
3,000-game analysis. The new graph is deliberately sparse and has no direct
2100-vs-2300 edge, so it can establish separation from 1600 and quantify
compression, but it cannot order 2100 and 2300 directly.

## Relationship to the original findings

The original study found that Maia 3 preserved 46.5% of the nominal 1100–1900
endpoint span and had a fitted Bradley–Terry slope of 0.476 over its preregistered
graph. This follow-up reaches beyond 1900 and again finds meaningful separation
without literal Elo calibration: the nominal 1600–2100 and 1600–2300 gaps retain
52.1% and 35.2%, respectively, under the descriptive score-to-Elo transform.

The appendix's three-label Bradley–Terry slope is 0.384, but it is not a formal
change-point estimate or a directly comparable replacement for the original
slope. The 1600 anchor was not part of the original within-family graph, and
the follow-up fit is saturated by only two scheduled edges.

## Completion and integrity

The frozen study completed all 400 games at 2026-09-01 22:17:31 UTC
(2026-09-02 07:17:31 JST). Launchd exited cleanly with status 0 and no
benchmark process remained after completion.

Both expected PGNs passed the preregistered integrity checks:

- exactly 200 games per PGN and 400 games total;
- rounds exactly 1 through 200 in order;
- OpeningIndex 1 through 100 exactly twice per matchup, with the players'
  colors reversed within every pair;
- one nonempty configuration hash per matchup;
- all results resolved and all player labels and Elo headers correct;
- every game starts with its indexed prefix from the frozen 100-opening suite;
- frozen suite SHA-256
  `3ad5d17fcd30bac36ef7277b15232e7df27bdb0728faa9ab441503d826cbc171`;
- no game/tool failures and no 300-ply cutoffs (maximum observed: 185 plies).

There was one operational deviation: the first launch invocation exited before
creating a game and logged a blank error. Launchd restarted it after 31 seconds.
No result was lost or duplicated, and the successful run then completed without
an in-game failure.

## Matchup results

All W/D/L figures are from the 1600 profile's perspective. Confidence intervals
are 95% percentile intervals from 20,000 resamples of the 100 paired openings,
keeping each color-reversed pair together.

| Matchup | W/D/L | 1600 score (95% CI) | Higher profile realized advantage (95% CI) | Compression (95% CI) |
|---|---:|---:|---:|---:|
| 1600 vs 2100 | 23/27/150 | 18.25% (13.75–23.00%) | 260.5 Elo (209.9–319.0) | 52.1% (42.0–63.8%) |
| 1600 vs 2300 | 26/26/148 | 19.50% (15.00–24.00%) | 246.3 Elo (200.2–301.3) | 35.2% (28.6–43.0%) |

The paired sign-flip p-value was at the Monte Carlo floor for each matchup
(`p = 0.000010` raw; `p = 0.000020` after Holm correction across the two
tests). Thus, the 1600 profile scored decisively below 50% against both higher
profiles.

The central finding is strong separation of 1600 from both higher conditioning
labels, but substantial compression relative to the nominal 500- and 700-point
label gaps. The study does not establish that 2300 is stronger than 2100. In
fact, the 1600 profile's observed score was slightly higher against 2300 than
against 2100, so the shared-anchor point estimate puts 2300 about 14 Elo below
2100. That comparison is indirect, was not a direct scheduled matchup, and
should not be treated as evidence of a reversed ordering.

These are engine-relative full-game results under the frozen deterministic
settings. Maia conditioning labels are not demonstrated human Elo ratings.

## Secondary model summaries

The draw-as-half-point Bradley–Terry fit, anchored at 1600, estimated relative
strengths of 0.0, +260.5, and +246.3 Elo for labels 1600, 2100, and 2300. Its
strength-on-label slope was 0.384 (paired-opening bootstrap 95% CI 0.327–0.451).
Because only the two edges through 1600 were played, this is a saturated fit;
the 2100–2300 difference is entirely indirect.

The draw-aware Davidson fit was stable. It estimated relative strengths of
0.0, +322.8, and +304.7 Elo, a strength-on-label slope of 0.476, and draw
parameter nu = 0.439. It yields the same substantive interpretation: both
higher profiles clearly separate from 1600, while no direct evidence orders
2100 and 2300.

BayesianElo was not installed on the analysis host, so that optional sensitivity
check was unavailable and omitted.

## Descriptive diagnostics

- Against 2100, the 1600 score was 16.5% as White and 20.0% as Black. Mean game
  length was 91.5 plies (median 93; range 17–183). Terminations: 173 checkmates,
  17 threefold repetitions, 5 stalemates, and 5 insufficient-material draws.
- Against 2300, the 1600 score was 21.5% as White and 17.5% as Black. Mean game
  length was 94.0 plies (median 93.5; range 17–185). Terminations: 174
  checkmates, 17 threefold repetitions, 4 stalemates, and 5
  insufficient-material draws.

## Reproducibility

The frozen plan is preserved in [the preregistration](preregistration.md)
(SHA-256 `c56734867a6193174df8c630991ed9cbbbd35d743f73c738215f4ddf2495ecd4`).
The analysis used seed `20260901`, 20,000 paired-opening bootstrap resamples,
and 100,000 paired sign flips. The complete PGNs are the primary records. The
reproducible script is [`analysis.py`](analysis.py); machine-readable outputs
and checksums are in [`data/`](data/), and exact Python package versions are in
[`requirements.txt`](requirements.txt).

From this directory, reproduce the validation and analysis with:

```bash
python3 -m venv .analysis-venv
.analysis-venv/bin/pip install -r requirements.txt
.analysis-venv/bin/python analysis.py
cd data && shasum -a 256 -c SHA256SUMS
```

Published data:

- [`maia3-1600__vs__maia3-2100.pgn`](data/maia3-1600__vs__maia3-2100.pgn)
- [`maia3-1600__vs__maia3-2300.pgn`](data/maia3-1600__vs__maia3-2300.pgn)
- [`games.csv`](data/games.csv) — one row per game
- [`matchups.csv`](data/matchups.csv) — results, intervals, color splits,
  realized gaps, and compression ratios
- [`pvalues.csv`](data/pvalues.csv) — paired sign-flip and Holm-adjusted p-values
- [`integrity.json`](data/integrity.json) — machine-readable validation record
- [`summary.json`](data/summary.json) — full machine-readable analysis summary
- [`SHA256SUMS`](data/SHA256SUMS) — hashes for the two PGNs and all derived data
