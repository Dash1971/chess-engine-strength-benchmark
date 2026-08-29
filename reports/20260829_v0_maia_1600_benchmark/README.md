# Maia 1600 Engine-Profile Benchmark

This report demonstrates a complete use of
[`chess-engine-strength-benchmark`](../../README.md): 600 games across four Maia
engine profiles, with every game preserved in PGN and game-level CSV form.

## Executive summary

The Maia3 1600 argmax profile finished first with a 56.0% aggregate score. Maia3
1600 balanced without a book placed second at 53.8%, followed by Maia3 balanced
with a book at 49.7%. Maia2 1600 with a book finished fourth at 40.5%.

The clearest pairwise findings were:

- Maia3 balanced with a book scored 62.5% against Maia2 with a book. Its
  bootstrap 95% interval was 54.5%–70.5%.
- Maia3 balanced without a book scored 59.0% against the otherwise identical
  Maia3 balanced profile with a book. Its interval was 50.5%–67.5%.
- The apparent advantages of argmax over the two balanced Maia3 profiles were
  smaller, and both 95% intervals included 50%. Those comparisons are
  inconclusive at 100 games.

These are results for the exact configurations below—not calibrated human Elo
ratings or general claims about Maia2, Maia3, argmax play, or opening books.

## Profiles

All four profiles were conditioned at Elo 1600. Maia3 used the upstream 79M
model. `SelfElo` and `OppoElo` were both 1600.

| Profile | Engine settings | Opening book |
|---|---|---|
| Maia2 1600 + book | `Elo=1600` | Rapid 1600 |
| Maia3 1600 balanced + book | `Elo=1600`, `SelfElo=1600`, `OppoElo=1600`, `Temperature=0.5`, `TopP=0.9` | Rapid 1600 |
| Maia3 1600 balanced, no book | Same balanced Maia3 settings | None |
| Maia3 1600 argmax + book | `Elo=1600`, `SelfElo=1600`, `OppoElo=1600`, `Temperature=0`, `TopP=1` | Rapid 1600 |

The book was `lichess_1600_rapid_2026-05.bin`, SHA-256
`9d64a44813a636998b6c6bf31380d806a9f3e1a26402e25de425950e62683bc6`.
The Maia3 79M checkpoint SHA-256 was
`3fc6181d5db789b45a15305732148757ae74efa3e0028e81ba335b462dac45c2`.

## Methodology

- Date: 29 August 2026 (Japan time).
- Runner: repository commit `86ada9a603203b634d86968be9e165563d23c0b9`.
- Design: complete four-profile round robin, six matchups, 100 games per
  matchup, 600 games total.
- Colors: each profile played exactly 50 White and 50 Black games per matchup.
- Search limit: one requested node per non-book move.
- Maximum length: 300 plies; no game reached the cutoff.
- Book selection: weighted random Polyglot selection with benchmark seed
  `20260829`. Each book-enabled side stopped using its book when its current
  position had no entry.
- Execution: matchups ran sequentially. Each matchup used two persistent UCI
  processes, which were closed before the next matchup.
- Hardware: 2020 13-inch MacBook Pro (`MacBookPro16,2`), quad-core 2 GHz Intel
  Core i5 with 16 GB RAM, running macOS 26.6.2.
- Runtime: Python 3.12.14, `chess` 1.11.2, PyTorch 2.2.2, CPU inference.
- Statistical intervals: game scores (1, 0.5, 0) were resampled independently
  20,000 times with a fixed seed; the 2.5th and 97.5th percentiles form the
  reported 95% bootstrap interval. Elo differences are the logistic transform
  of score percentages and should be treated as descriptive estimates.

## Overall standings

Each profile played 300 games.

| Rank | Profile | W | D | L | Score |
|---:|---|---:|---:|---:|---:|
| 1 | Maia3 1600 argmax + book | 135 | 66 | 99 | 56.0% |
| 2 | Maia3 1600 balanced, no book | 129 | 65 | 106 | 53.8% |
| 3 | Maia3 1600 balanced + book | 115 | 68 | 117 | 49.7% |
| 4 | Maia2 1600 + book | 85 | 73 | 142 | 40.5% |

The standings summarize this closed four-profile field. They do not assign an
absolute rating to any engine.

## Pairwise results

Results are shown from the first-listed profile's perspective. `Δ Elo` is also
first-listed minus second-listed.

| First profile | Second profile | W–D–L | Score (95% interval) | Δ Elo (95% interval) |
|---|---|---:|---:|---:|
| Maia2 + book | Maia3 argmax + book | 31–23–46 | 42.5% (34.0%–51.0%) | −53 (−115–+7) |
| Maia2 + book | Maia3 balanced + book | 24–27–49 | 37.5% (29.5%–45.5%) | −89 (−151–−31) |
| Maia2 + book | Maia3 balanced, no book | 30–23–47 | 41.5% (33.0%–50.0%) | −60 (−123–0) |
| Maia3 balanced + book | Maia3 argmax + book | 35–21–44 | 45.5% (37.0%–54.5%) | −31 (−92–+31) |
| Maia3 balanced + book | Maia3 balanced, no book | 31–20–49 | 41.0% (32.5%–49.5%) | −63 (−127–−3) |
| Maia3 balanced, no book | Maia3 argmax + book | 33–22–45 | 44.0% (35.5%–52.5%) | −42 (−104–+17) |

## Insights

### Maia3 led Maia2 in all three comparisons

All Maia3 profiles scored above 50% against Maia2. Only Maia3 balanced with a
book had a 95% interval wholly above 50%; the other two intervals touched or
crossed 50%. The consistent direction is notable, but 100 games remains a
modest sample for the closer comparisons.

### The Rapid 1600 book did not improve balanced Maia3 in this experiment

Balanced Maia3 without a book scored 59.0% head-to-head against balanced Maia3
with the book. This is evidence about this particular book, engine, sampling
policy, and runner behavior—not evidence that opening books generally weaken
Maia. A larger paired-opening experiment is the right follow-up.

### Argmax ranked first, but its Maia3 head-to-head margins are uncertain

Argmax scored 54.5% against balanced+book and 56.0% against balanced-no-book.
Both intervals included 50%, so the experiment does not establish a reliable
argmax advantage over either balanced profile. More games should target these
two comparisons rather than rerunning the whole matrix.

### Color mattered

White scored 55.3% overall (264 wins, 136 draws, 200 losses). Alternating colors
prevented unequal color allocation, but it did not create paired games from the
same opening. Exact reversed-opening pairs would reduce opening variance and
support stronger profile comparisons.

### Engine mix dominated throughput

The three Maia2-vs-Maia3 matches ran at 202–210 games/hour. The three
Maia3-vs-Maia3 matches ran at only 96–104 games/hour because two 79M models were
performing CPU inference. Total engine time was 4h27m47s, or 134.4 games/hour.
Runtime estimates therefore need to account for the engines in each matchup,
not only the number of games.

## Game characteristics

- 464 checkmates (77.3%)
- 113 threefold repetitions (18.8%)
- 14 stalemates (2.3%)
- 9 insufficient-material draws (1.5%)
- Mean game length: 86.3 plies; median: 82.5; range: 11–234
- Engine crashes: 0
- Illegal moves: 0
- Unresolved games: 0
- Maximum-ply adjudications: 0

## Runner observations and proposed improvements

The published two-engine tool completed all 600 games without a chess or engine
failure. Its small interface and direct PGN output worked well for one matchup
at a time. The run also identified several worthwhile improvements for a future
version:

1. **Flush and checkpoint each completed game.** The PGN and console output were
   block-buffered during these long matches. An interruption could lose the
   whole in-progress file, and there was no durable progress indicator.
2. **Resume safely.** The runner currently opens its output in write mode. It
   should validate an existing PGN, resume from the next game, and preserve the
   intended color balance and random state.
3. **Support paired reversed openings.** Color alternation alone does not replay
   the same opening with colors swapped. A paired-opening mode would materially
   improve comparative precision.
4. **Record the effective configuration.** A sidecar manifest should capture
   runner commit, CLI arguments, engine IDs/options, file hashes, seed, software,
   hardware, and timestamps without embedding private local paths.
5. **Expose useful progress.** Games completed, elapsed time, throughput, and an
   estimated finish time should be visible and flushed immediately.
6. **Clarify randomness.** The benchmark seed controls Polyglot choices but does
   not necessarily seed stochastic behavior inside an engine. The tool should
   document that distinction and pass an engine seed when supported.
7. **Make CPU use controllable.** Neither Maia launcher exposed a UCI `Threads`
   option, and PyTorch used multiple CPU threads even though the runner requested
   one search node. Environment-level thread limits or launcher guidance would
   make concurrent experiments more predictable.
8. **Report book provenance.** Recording the ply where each side left its book
   would make book/no-book results easier to interpret.

These are proposals only; this report does not change the published runner.

## Limitations

- Games within a matchup were not paired by an identical opening followed by a
  color reversal.
- Book moves were sampled independently. The same seed does not guarantee the
  same opening across profiles with different book availability.
- Maia3 balanced play is stochastic, and the runner did not control the
  engine's internal random seed.
- Bootstrap intervals treat game results as independent observations. Repeated
  or related opening lines can reduce the effective sample size.
- One hundred games provides limited power for small differences. Pairwise
  intervals are more informative than the rank order alone.
- The test used one CPU machine and one-node moves. Results and throughput may
  differ under other software, hardware, or search limits.
- Elo conditioning tells Maia which human rating style to model; it is not a
  promise that the profile has that engine-vs-engine playing strength.

## Appendix: complete data

The appendix contains all 600 games and every derived table:

- [`games.csv`](data/games.csv) — one row per game with matchup, colors, result,
  termination, ply count, Elo headers, first-listed engine score, and source PGN
- [`matchups.csv`](data/matchups.csv) — pairwise results, intervals, color splits,
  Elo transforms, runtime, and throughput
- [`standings.csv`](data/standings.csv) — aggregate standings
- [`terminations.csv`](data/terminations.csv) — termination distribution
- [`summary.json`](data/summary.json) — machine-readable report summary
- [`SHA256SUMS`](data/SHA256SUMS) — integrity hashes for every CSV, JSON, and PGN
- [`maia2-book__vs__maia3-argmax-book.pgn`](data/maia2-book__vs__maia3-argmax-book.pgn)
- [`maia2-book__vs__maia3-balanced-book.pgn`](data/maia2-book__vs__maia3-balanced-book.pgn)
- [`maia2-book__vs__maia3-balanced-no-book.pgn`](data/maia2-book__vs__maia3-balanced-no-book.pgn)
- [`maia3-balanced-book__vs__maia3-argmax-book.pgn`](data/maia3-balanced-book__vs__maia3-argmax-book.pgn)
- [`maia3-balanced-book__vs__maia3-balanced-no-book.pgn`](data/maia3-balanced-book__vs__maia3-balanced-no-book.pgn)
- [`maia3-balanced-no-book__vs__maia3-argmax-book.pgn`](data/maia3-balanced-no-book__vs__maia3-argmax-book.pgn)

The CSV and JSON tables are derived from the PGNs. The six PGNs are the primary
game records.
