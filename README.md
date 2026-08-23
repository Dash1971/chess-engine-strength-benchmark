# chess-engine-strength-benchmark

A simple command-line program for playing a color-balanced match between two
installed UCI chess engines.

It alternates colors automatically, prints the result of each game, summarizes
Engine A's wins, draws, losses, win percentage, and score percentage, and saves
every game to one PGN file.

## Prerequisites

- Python 3.9 or newer
- two working UCI engine launchers
- optional Polyglot opening books (`.bin`)

This project does not install Maia. For a complete local Maia 3 installation,
see [maia3-local-stack](https://github.com/Dash1971/maia3-local-stack).

## Installation

```bash
git clone https://github.com/Dash1971/chess-engine-strength-benchmark.git
cd chess-engine-strength-benchmark
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Example

This runs 100 games between Maia 3 1600 and Maia 2 1900. Each engine uses its
own opening book. Engine A plays 50 games as White and 50 as Black.

```bash
.venv/bin/maia-benchmark \
  --engine-a-path ~/chess/maia3-engine/maia3-engine.sh \
  --engine-a-name "Maia3 1600 balanced" \
  --engine-a-elo 1600 \
  --engine-a-self-elo 1600 \
  --engine-a-opponent-elo 1600 \
  --engine-a-temperature 0.5 \
  --engine-a-top-p 0.9 \
  --engine-a-book ~/chess/books/Rapid/2026/lichess_1600_rapid_2026-05.bin \
  --engine-b-path ~/chess/maia2-engine/maia2-engine.sh \
  --engine-b-name "Maia2 1900" \
  --engine-b-elo 1900 \
  --engine-b-book ~/chess/books/Rapid/2026/lichess_1900_rapid_2026-05.bin \
  --number-of-games 100 \
  --output maia3-1600-vs-maia2-1900.pgn
```

The number of games must be even so the color split is exactly 50/50.

## Engine options

Every engine option has an A and B version:

- `--engine-a-path` / `--engine-b-path` — UCI launcher (required)
- `--engine-a-name` / `--engine-b-name` — label used in output and PGN
- `--engine-a-elo` / `--engine-b-elo` — Maia Elo setting
- `--engine-a-self-elo` / `--engine-b-self-elo` — Maia 3 SelfElo
- `--engine-a-opponent-elo` / `--engine-b-opponent-elo` — Maia 3 OppoElo
- `--engine-a-temperature` / `--engine-b-temperature` — Maia 3 Temperature
- `--engine-a-top-p` / `--engine-b-top-p` — Maia 3 TopP
- `--engine-a-book` / `--engine-b-book` — optional Polyglot book

Only specify options supported by the selected engine. Option names are matched
case-insensitively, so `ELO` and `Elo` are both handled.

Match options:

- `--number-of-games` — even number of games (required)
- `--output` — PGN path; defaults to `benchmark-games.pgn`
- `--nodes` — nodes requested per move; defaults to `1`
- `--move-time-ms` — use a time limit per move instead of `--nodes`
- `--max-plies` — draw cutoff; defaults to `300`
- `--seed` — optional reproducible seed for opening-book choices

Run `maia-benchmark --help` for the complete CLI reference.

## Output

During the match:

```text
Game 1/100: 1-0 (Maia3 1600 balanced vs Maia2 1900)
Game 2/100: 1/2-1/2 (Maia2 1900 vs Maia3 1600 balanced)
```

At the end:

```text
Match complete
Engine A: Maia3 1600 balanced
Engine B: Maia2 1900
Engine A result: 33 wins / 36 draws / 31 losses
Win percentage: 33.0%
Score percentage: 51.0%
Elapsed: 2089.0 seconds
PGN: /path/to/maia3-1600-vs-maia2-1900.pgn
```

`Win percentage` counts wins only. `Score percentage` uses standard chess
scoring: one point for a win and half a point for a draw.

## License

Code in this repository is released under the MIT License. Maia model weights
retain their upstream licenses. Lichess database exports are CC0.
