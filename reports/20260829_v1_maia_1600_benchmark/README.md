# Maia 1600 Engine-Profile Benchmark — Expanded Report

This expanded report demonstrates a complete use of
[`chess-engine-strength-benchmark`](../../README.md): 1,000 games across five
Maia engine profiles, with every game preserved in PGN and game-level CSV form.
It supersedes the original [600-game v0 report](../20260829_v0_maia_1600_benchmark/README.md)
by adding Maia3 1600 argmax without a book and its four matchups.

## Executive summary

Maia3 1600 argmax with a book retained first place with a 55.9% aggregate
score. Maia3 balanced without a book placed second at 53.8%, followed by the
new Maia3 argmax without a book profile at 52.0%. Maia3 balanced with a book
scored 49.8%, and Maia2 with a book scored 38.6%.

The added profile clarified the experiment:

- Argmax without a book scored 67.0% against Maia2 with a book, the largest
  Maia3–Maia2 margin in the matrix.
- Argmax without a book tied balanced with a book exactly, 50.0%.
- Balanced without a book scored 53.5% against argmax without a book.
- Argmax with a book scored 55.5% against argmax without a book. Its bootstrap
  95% interval was 46.5%–64.0%, so the observed advantage remains inconclusive.

Book effects were not consistent across policies: no-book beat book in the
balanced comparison, while book led no-book in the argmax comparison. Neither
result supports a general claim that opening books help or hurt Maia3.

These are results for the exact configurations below—not calibrated human Elo
ratings or general claims about Maia2, Maia3, argmax play, or opening books.

## Profiles

All five profiles were conditioned at Elo 1600. Maia3 used the upstream 79M
model. `SelfElo` and `OppoElo` were both 1600.

| Profile | Engine settings | Opening book |
|---|---|---|
| Maia2 1600 + book | `Elo=1600` | Rapid 1600 |
| Maia3 1600 balanced + book | `Elo=1600`, `SelfElo=1600`, `OppoElo=1600`, `Temperature=0.5`, `TopP=0.9` | Rapid 1600 |
| Maia3 1600 balanced, no book | Same balanced Maia3 settings | None |
| Maia3 1600 argmax + book | `Elo=1600`, `SelfElo=1600`, `OppoElo=1600`, `Temperature=0`, `TopP=1` | Rapid 1600 |
| Maia3 1600 argmax, no book | Same argmax Maia3 settings | None |

The book was `lichess_1600_rapid_2026-05.bin`, SHA-256
`9d64a44813a636998b6c6bf31380d806a9f3e1a26402e25de425950e62683bc6`.
The Maia3 79M checkpoint SHA-256 was
`3fc6181d5db789b45a15305732148757ae74efa3e0028e81ba335b462dac45c2`.

## Methodology

- Date: 29 August 2026 (Japan time).
- Runner: repository commit `86ada9a603203b634d86968be9e165563d23c0b9`.
- Design: complete five-profile round robin, ten matchups, 100 games per
  matchup, 1,000 games total.
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

Each profile played 400 games.

| Rank | Profile | W | D | L | Score |
|---:|---|---:|---:|---:|---:|
| 1 | Maia3 1600 argmax + book | 180 | 87 | 133 | 55.9% |
| 2 | Maia3 1600 balanced, no book | 174 | 82 | 144 | 53.8% |
| 3 | Maia3 1600 argmax, no book | 164 | 88 | 148 | 52.0% |
| 4 | Maia3 1600 balanced + book | 152 | 94 | 154 | 49.8% |
| 5 | Maia2 1600 + book | 106 | 97 | 197 | 38.6% |

The standings summarize this closed five-profile field. They do not assign an
absolute rating to any engine.

## Pairwise results

Results are shown from the first-listed profile's perspective. `Δ Elo` is also
first-listed minus second-listed.

| First profile | Second profile | W–D–L | Score (95% interval) | Δ Elo (95% interval) |
|---|---|---:|---:|---:|
| Maia2 + book | Maia3 argmax + book | 31–23–46 | 42.5% (34.0%–51.0%) | −53 (−115–+7) |
| Maia2 + book | Maia3 argmax, no book | 21–24–55 | 33.0% (25.5%–41.0%) | −123 (−186–−63) |
| Maia2 + book | Maia3 balanced + book | 24–27–49 | 37.5% (29.5%–45.5%) | −89 (−151–−31) |
| Maia2 + book | Maia3 balanced, no book | 30–23–47 | 41.5% (33.0%–50.0%) | −60 (−123–0) |
| Maia3 argmax + book | Maia3 argmax, no book | 45–21–34 | 55.5% (46.5%–64.0%) | +38 (−24–+100) |
| Maia3 balanced + book | Maia3 argmax + book | 35–21–44 | 45.5% (37.0%–54.0%) | −31 (−92–+28) |
| Maia3 balanced + book | Maia3 argmax, no book | 37–26–37 | 50.0% (41.5%–58.5%) | 0 (−60–+60) |
| Maia3 balanced + book | Maia3 balanced, no book | 31–20–49 | 41.0% (32.5%–50.0%) | −63 (−127–0) |
| Maia3 balanced, no book | Maia3 argmax + book | 33–22–45 | 44.0% (35.5%–52.5%) | −42 (−104–+17) |
| Maia3 balanced, no book | Maia3 argmax, no book | 45–17–38 | 53.5% (44.5%–62.5%) | +24 (−38–+89) |

## Insights

### Maia3 led Maia2 in all four comparisons

All Maia3 profiles scored above 50% against Maia2. The largest margin belonged
to argmax without a book, which scored 67.0% with a 59.0%–74.5% interval. Maia3
balanced with a book was the other comparison whose interval was wholly above
50%. The consistent direction is notable, but it applies to these profiles and
this engine-vs-engine setup—not to human predictive accuracy.

### The completed 2×2 design shows a policy–book interaction

The four Maia3 configurations now cover both policies with and without the
Rapid 1600 book. Balanced no-book beat balanced book 59.0%–41.0%, while argmax
book led argmax no-book 55.5%–44.5%. The argmax interval included 50%, and the
runner did not use paired openings, so the evidence does not establish opposite
causal book effects. It does show that “book” cannot be treated as one simple,
policy-independent strength adjustment.

### Argmax without a book was not uniformly strongest

Despite its decisive Maia2 result, argmax no-book tied balanced book, trailed
balanced no-book 46.5%–53.5%, and trailed argmax book 44.5%–55.5%. Both losses
had intervals containing 50%. Its third-place aggregate finish is therefore a
useful warning against ranking profiles from one opponent alone.

### The top two positions did not change

Argmax with a book remained first, and balanced without a book remained second.
However, their direct match still favored argmax only 56.0%–44.0% with an
interval that included 50%. The rank order is descriptive, not proof of a
stable strength hierarchy among the closer Maia3 profiles.

### Color mattered

White scored 56.5% overall (453 wins, 224 draws, 323 losses). Alternating colors
prevented unequal color allocation, but it did not create paired games from the
same opening. Exact reversed-opening pairs would reduce opening variance and
support stronger profile comparisons.

### Engine mix dominated throughput

Maia2-vs-Maia3 matches ran at 178–210 games/hour. Maia3-vs-Maia3 matches ran at
only 90–104 games/hour because two 79M models were performing CPU inference.
Total engine time for all 1,000 games was 8h18m35s, or 120.3 games/hour. The
400-game expansion took 3h50m48s.

## Game characteristics

- 776 checkmates (77.6%)
- 190 threefold repetitions (19.0%)
- 21 stalemates (2.1%)
- 13 insufficient-material draws (1.3%)
- Mean game length: 86.9 plies; median: 83; range: 11–234
- Engine crashes: 0
- Illegal moves: 0
- Unresolved games: 0
- Maximum-ply adjudications: 0

## Runner observations and proposed improvements

The published two-engine tool completed all 1,000 games without a chess or
engine failure. Its small interface and direct PGN output worked well for one
matchup at a time. The run also identified several worthwhile improvements for
a future version:

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

The appendix contains all 1,000 games and every derived table:

- [`games.csv`](data/games.csv) — one row per game with matchup, colors, result,
  termination, ply count, Elo headers, first-listed engine score, and source PGN
- [`matchups.csv`](data/matchups.csv) — pairwise results, intervals, color splits,
  Elo transforms, runtime, and throughput
- [`standings.csv`](data/standings.csv) — aggregate standings
- [`terminations.csv`](data/terminations.csv) — termination distribution
- [`summary.json`](data/summary.json) — machine-readable report summary
- [`SHA256SUMS`](data/SHA256SUMS) — integrity hashes for every CSV, JSON, and PGN

The ten PGNs in [`data/`](data/) are the primary game records. The CSV and JSON
tables are derived from them.
