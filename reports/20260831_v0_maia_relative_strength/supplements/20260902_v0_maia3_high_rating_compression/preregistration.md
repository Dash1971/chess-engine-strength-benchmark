# Maia 3 high-rating compression follow-up: preregistration

## Purpose

This follow-up measures the relative full-game playing-strength separation of
deterministic Maia 3 profiles conditioned at 1600, 2100, and 2300. It directly
tests the 1600-vs-2100 and 1600-vs-2300 gaps. It deliberately does not run or
claim a direct 2100-vs-2300 comparison.

The ratings are Maia conditioning labels, not demonstrated human Elo ratings.
The study measures engine-relative full-game behavior under the frozen settings
below; it does not measure human move-prediction accuracy.

This document is frozen before either core PGN exists. The UCI readiness check
performed before freezing produced one move from a starting-position test and
is excluded from the study.

## Frozen engine and host

- Maia 3 upstream repository commit:
  `1e13597c42d4858b7cfd7cfdae01e297263364b2`
- Local `maia3/models.py` SHA-256:
  `b95456e742a8305316de1afb0f35197b7a815f909c54dcb8c97e3c452273432c`
- The sole source modification is the previously disclosed RMSNorm
  compatibility implementation required by PyTorch 2.2 on Intel macOS.
- Maia 3 79M checkpoint SHA-256:
  `3fc6181d5db789b45a15305732148757ae74efa3e0028e81ba335b462dac45c2`
- Engine launcher SHA-256:
  `a0580532a1925e9b965e378435d51defcbb6f8f4d4c4e3132eb75085144b93c4`
- Benchmark repository commit:
  `3dcca39b5911ca951df62f23de689e45c4237830`
- Python 3.12, python-chess 1.11.2, PyTorch 2.2.2, CPU inference.
- Host: MacBookPro16,2, quad-core Intel Core i5-1038NG7, 16 GB RAM,
  macOS 26.6.2.

Every profile uses the 79M checkpoint, UCI history, `Temperature=0`, `TopP=1`,
one requested node per move, no opening book, and a 300-ply draw limit. Each
engine receives its own label as `SelfElo` and its opponent's label as
`OppoElo`.

## Frozen match schedule

1. Maia 3 1600 vs Maia 3 2100
2. Maia 3 1600 vs Maia 3 2300

Each matchup contains 200 games, for 400 core games total. No matchup may be
added, removed, extended, or stopped based on interim results.

## Opening control

Both matchups use the existing 100-prefix suite:
`openings/maia-relative-strength-100.pgn`.

Suite SHA-256:
`3ad5d17fcd30bac36ef7277b15232e7df27bdb0728faa9ab441503d826cbc171`.

Every prefix is played twice with colors reversed. The suite and schedule are
identical across both matchups.

## Integrity and recovery rules

- Completed games are flushed and fsynced after every game.
- Interrupted matches resume only through the benchmark's validating
  `--resume` mode.
- Resume must reject changes to player labels, executable paths, Elo inputs,
  sampling settings, opening suite, limits, or game count.
- A completed game is excluded only if it is unresolved, violates the frozen
  opening/color schedule, has a configuration-hash mismatch, or reflects a
  documented engine/tool failure.
- A failed unfinished game may be replayed under the identical configuration;
  failures and recoveries will be disclosed.
- No interim chess result will be analyzed before all 400 games are complete.

## Frozen analysis

For each matchup, report W/D/L from the 1600 profile's perspective, score,
color split, termination distribution, game length, and descriptive realized
Elo using `400 * log10(p / (1 - p))`.

Compression ratios are the higher profile's realized Elo advantage divided by
the nominal gap: 500 points for 1600-vs-2100 and 700 points for
1600-vs-2300.

Uncertainty uses 20,000 percentile-bootstrap resamples of the 100 opening pairs
as clusters, keeping both color-reversed games together. Direction tests use
100,000 paired sign flips around 50%, with Holm adjustment across the two
matchups. The fixed analysis seed is `20260901`.

A three-node Bradley-Terry curve will be fitted with draws worth half a point,
anchored at 1600, and its strength-on-label slope reported as a secondary global
summary. A draw-aware Davidson fit and BayesianElo will be reported as
sensitivity checks if stable. Because there is no direct 2100-vs-2300 match,
their difference is indirect through the shared 1600 anchor and will be labeled
accordingly.

The final report will distinguish monotonic evidence from exact human-rating
calibration and will disclose operational deviations and model-fit limitations.
