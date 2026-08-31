# Maia 2 and Maia 3 Relative-Strength Study

This preregistered study measures how much relative full-game playing-strength
separation Maia 2 and Maia 3 preserve across nominal settings from 1100 to 1900.
It contains 3,000 games: 15 matchups, 200 games per matchup, and 100 fixed
opening prefixes played once with each engine-color assignment.

## Executive summary

Maia 3 preserved substantially more of the nominal rating scale than Maia 2.
The Bradley–Terry fitted strength-on-label slope was **0.476** for Maia 3 and
**0.177** for Maia 2. Their difference was **0.299**, with a paired-opening
cluster-bootstrap 95% interval of **0.217–0.388**. A draw-aware Davidson fit
gave the same conclusion: slopes of 0.615 and 0.274, respectively.

The direct 1100-vs-1900 match told the same story:

- Maia 2 1100 scored 30.75% against Maia 2 1900, a descriptive realized gap
  of 141 Elo, or 17.6% of the nominal 800-point span.
- Maia 3 1100 scored 10.50% against Maia 3 1900, a descriptive realized gap
  of 372 Elo, or 46.5% of the nominal span.

Both families were monotonic in the fitted model, but Maia 2 was highly
compressed. Its 1300–1500 and 1700–1900 direct matches were essentially flat.
All four Maia 3 adjacent bands favored the higher setting after Holm correction.

At equal labels, Maia 2 and Maia 3 were level at 1100 and 1300. Maia 3 then led
increasingly at 1500, 1700, and 1900. After correction across the five equal-label
tests, the Maia 3 advantage was resolved at 1700 and 1900, but not at 1500.

These are **engine-relative measurements for the exact configurations below**.
They do not show that a nominal Maia 1500 plays like a 1500-rated human, nor do
they measure human move-prediction quality.

## Primary family results

| Model | Maia 2 | Maia 3 | Maia 3 − Maia 2 |
|---|---:|---:|---:|
| Bradley–Terry slope | 0.177 | 0.476 | +0.299 |
| Paired-bootstrap 95% interval | 0.132–0.224 | 0.409–0.553 | 0.217–0.388 |
| Davidson sensitivity slope | 0.274 | 0.615 | +0.341 |
| Direct 1100–1900 realized gap | 141 Elo | 372 Elo | +231 Elo |
| Direct endpoint compression ratio | 0.176 | 0.465 | +0.289 |

The bootstrap comparison used 20,000 resamples of the 100 opening pairs within
each matchup. The two-sided bootstrap tail probability for the slope difference
was below 0.0001 at that resolution.

## Fitted relative strength curves

Strengths are normalized to zero at each family's 1100 setting. The ordinary
Bradley–Terry fit treats a draw as half a point.

| Nominal setting | Maia 2 fitted Elo | Maia 3 fitted Elo |
|---:|---:|---:|
| 1100 | 0 | 0 |
| 1300 | 59 | 100 |
| 1500 | 73 | 176 |
| 1700 | 131 | 300 |
| 1900 | 141 | 376 |

The graph fit was internally consistent: score residual RMSE was 0.02 percentage
points for Maia 2 and 0.21 percentage points for Maia 3. The draw-aware Davidson
model increased both fitted scales but retained a clear Maia 3 advantage.

## Within-family matches

Results are from the lower nominal setting's perspective. `Gap` is the
descriptive logistic Elo advantage of the higher setting. Intervals resample
the 100 paired openings as clusters.

| Family | Match | W–D–L | Lower score (95% interval) | Gap | Preserved |
|---|---:|---:|---:|---:|---:|
| Maia 2 | 1100–1300 | 46–74–80 | 41.50% (36.50–46.50%) | 60 | 29.8% |
| Maia 2 | 1300–1500 | 64–64–72 | 48.00% (42.75–53.25%) | 14 | 7.0% |
| Maia 2 | 1500–1700 | 49–69–82 | 41.75% (36.50–47.00%) | 58 | 28.9% |
| Maia 2 | 1700–1900 | 64–66–70 | 48.50% (43.00–54.00%) | 10 | 5.2% |
| Maia 2 | 1100–1900 | 28–67–105 | 30.75% (26.25–35.25%) | 141 | 17.6% |
| Maia 3 | 1100–1300 | 46–51–103 | 35.75% (30.00–41.50%) | 102 | 50.9% |
| Maia 3 | 1300–1500 | 56–44–100 | 39.00% (33.75–44.25%) | 78 | 38.9% |
| Maia 3 | 1500–1700 | 49–33–118 | 32.75% (27.00–38.75%) | 125 | 62.5% |
| Maia 3 | 1700–1900 | 59–38–103 | 39.00% (33.25–45.00%) | 78 | 38.9% |
| Maia 3 | 1100–1900 | 14–14–172 | 10.50% (7.00–14.25%) | 372 | 46.5% |

Maia 2's best-preserved adjacent region was 1100–1300, closely followed by
1500–1700. Maia 3's best-preserved region was 1500–1700. This means closest to
the nominal 200-point separation within this engine-relative experiment; it is
not evidence of an accurate human-Elo region.

Paired sign-flip tests found resolved adjacent differences for Maia 2 at
1100–1300 (`Holm p=0.0060`) and 1500–1700 (`p=0.0112`), but not at 1300–1500
or 1700–1900. All four Maia 3 bands were resolved after correction
(`Holm p≤0.00067`).

## Equal-label cross-generation matches

Results are from Maia 2's perspective.

| Label | Maia 2 W–D–L | Maia 2 score (95% interval) | Holm p |
|---:|---:|---:|---:|
| 1100 | 74–49–77 | 49.25% (43.25–55.25%) | 1.0000 |
| 1300 | 76–48–76 | 50.00% (43.75–56.25%) | 1.0000 |
| 1500 | 67–43–90 | 44.25% (38.00–50.50%) | 0.2387 |
| 1700 | 46–57–97 | 37.25% (31.75–42.75%) | 0.00008 |
| 1900 | 36–46–118 | 29.50% (24.50–34.75%) | 0.00005 |

The widening Maia 3 advantage at higher labels supports increased dynamic
range, not a uniform generation-wide strength shift. Maia 3 was not detectably
weaker at the bottom: the 1100 and 1300 matches were effectively even.

## Game characteristics

- 3,000 resolved games; zero excluded games and zero 300-ply cutoffs
- 2,237 checkmates (74.6%)
- 666 threefold repetitions (22.2%)
- 79 stalemates (2.6%)
- 17 insufficient-material draws (0.6%)
- 1 fifty-move draw
- Mean game length: 84.6 plies; median: 81; range: 17–239

Every matchup contained exactly one configuration hash, all 100 opening indices,
and two games per opening with reversed engine colors.

## Methodology

- Core run: 30–31 August 2026 (Japan time).
- Frozen plan: [preregistration](../../docs/maia-relative-strength-preregistration.md).
- Runner: repository commit `991cbb7ab5eba8cb7680824d1f6355f1dab2e81b`.
- Design: 15 specified matchups, 200 games each, 3,000 games total.
- Opening control: 100 fixed eight-ply prefixes, each played twice with colors
  reversed; suite SHA-256
  `3ad5d17fcd30bac36ef7277b15232e7df27bdb0728faa9ab441503d826cbc171`.
- Search: one requested node per move; no opening books; 300-ply draw limit.
- Maia 2: Rapid model, separate self/opponent Elo conditioning; model SHA-256
  `65aae8465eed5e65df66a24ea7370715579f9e5435098d06fe18bdb1e267e997`.
- Maia 3: upstream 79M model, `Temperature=0`, `TopP=1`, UCI history enabled,
  separate self/opponent Elo conditioning; checkpoint SHA-256
  `3fc6181d5db789b45a15305732148757ae74efa3e0028e81ba335b462dac45c2`.
- Runtime: Python 3.12, `chess` 1.11.2, PyTorch 2.2.2, CPU inference.
- Hardware: 2020 13-inch MacBook Pro (`MacBookPro16,2`), quad-core 2 GHz
  Intel Core i5, 16 GB RAM, macOS 26.6.2.

### Statistical analysis

Scores were 1, 0.5, and 0. The two reversed-color games belonging to one
opening were kept together in all 20,000 percentile-bootstrap resamples.
Direction tests used 100,000 random paired sign flips around 50%; p-values were
Holm-adjusted within each four-match adjacent family and across the five
cross-generation matches. Fixed analysis seed: `20260831`.

For a score `p`, descriptive realized Elo is
`400 × log10(p / (1 − p))`. Bradley–Terry latent strengths maximize the
fractional-binomial likelihood with draws contributing half a point. The global
scale-preservation estimate is the ordinary least-squares slope of fitted
relative Elo on nominal rating. The slope interval resamples opening pairs
inside every family matchup and refits the full model. The Davidson sensitivity
model assigns a separate draw probability proportional to the geometric mean
of the two fitted abilities. Exact implementation is in [`analysis.py`](analysis.py).

## Operational deviations

The host launcher invoked the resume-safe runner 12 times during the study.
Eleven interrupted invocations lost only the unfinished game, if any; the
runner validated and skipped every durable completed game before continuing.
The final invocation was externally stopped for about 52 minutes and resumed
without restarting its process tree. No matchup, opening, engine setting, or
analysis rule changed; there were no logged engine failures, excluded completed
games, replacement games, duplicate rounds, or unresolved results.

The full wall-clock span was about 31 hours 19 minutes, so it should not be used
as a clean throughput benchmark. Maia 3-vs-Maia 3 CPU inference was the dominant
runtime cost.

## Interpretation and limitations

- The result measures full-game engine play, not human move-prediction accuracy.
- Nominal settings are conditioning labels, not demonstrated human Elo ratings.
- The shared opening suite controls openings but is not a representative sample
  of openings played by humans at any tested rating.
- One-node CPU games can rank configurations differently from other hardware,
  search limits, sampling policies, or model checkpoints.
- A descriptive Elo transform of game score is not a new absolute rating scale.
- The 15-match graph was selected in advance; untested nonadjacent bands may
  contain structure that this design cannot resolve.

## Reproduce and inspect

Create a separate environment and rerun the analysis from this directory:

```bash
python3 -m venv .analysis-venv
.analysis-venv/bin/pip install -r requirements.txt
.analysis-venv/bin/python analysis.py
cd data && shasum -a 256 -c SHA256SUMS
```

The data appendix contains:

- [`games.csv`](data/games.csv) — one row per game
- [`matchups.csv`](data/matchups.csv) — W/D/L, paired intervals, color splits,
  realized gaps, and compression ratios
- [`pvalues.csv`](data/pvalues.csv) — paired sign-flip and Holm-adjusted p-values
- [`bt_ratings.csv`](data/bt_ratings.csv) — Bradley–Terry and Davidson strengths
- [`bt_fit.csv`](data/bt_fit.csv) — observed/fitted scores and residuals
- [`family_summary.csv`](data/family_summary.csv) — slopes and uncertainty
- [`terminations.csv`](data/terminations.csv) — game-ending distribution
- [`summary.json`](data/summary.json) — machine-readable integrity summary
- [`SHA256SUMS`](data/SHA256SUMS) — hashes for all tables and 15 PGNs

The PGNs are the primary records. All tables are regenerated from them by the
published script.
