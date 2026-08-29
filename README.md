# chess-engine-strength-benchmark

A simple command-line program for playing a color-balanced match between two
installed UCI chess engines. It supports ordinary opening books or a fixed PGN
opening suite in which every opening is played twice with reversed engine
colors.

It alternates colors automatically, prints the result of each game, summarizes
Engine A's wins, draws, losses, win percentage, and score percentage, and saves
every game to one PGN file.

## Prerequisites

- Python 3.9 or newer
- two working UCI engine launchers
- optional Polyglot opening books (`.bin`)
- optional PGN opening suite for controlled paired matches

This project does not install Maia. For a complete local Maia 3 installation,
see [maia3-local-stack](https://github.com/Dash1971/maia3-local-stack).

## Installation

```bash
git clone https://github.com/Dash1971/chess-engine-strength-benchmark.git
cd chess-engine-strength-benchmark
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Graphical interface

Run the optional desktop interface with:

```bash
.venv/bin/maia-benchmark-gui
```

The GUI provides the same engine and match settings as the command line, file
pickers for launchers, books, opening suites, and output, plus live match output,
stop, resume, and a button to reveal the resulting PGN. It invokes the regular
`maia-benchmark` implementation, so GUI and command-line matches use the same
validation, pairing, checkpointing, and output format.

Tkinter is included with standard Python installers on macOS. Some minimal
Linux installations package it separately; on Debian and Ubuntu it can be
installed with `sudo apt install python3-tk`. A graphical desktop session is
required. The command-line interface remains available on headless machines.

Stopping terminates the running match process. Completed games have already
been flushed to the PGN; select the same opening suite and output, check
**Resume interrupted paired match**, and start again to continue safely.

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

## Controlled paired-opening example

For a controlled comparison, put one opening prefix in each game of a PGN file.
This example assumes `openings.pgn` contains 100 games and therefore runs 200
benchmark games: once per opening with Engine A as White and once with Engine B
as White.

```bash
.venv/bin/maia-benchmark \
  --engine-a-path ~/chess/maia3-engine/maia3-engine.sh \
  --engine-a-name "Maia3 1100" \
  --engine-a-elo 1100 \
  --engine-a-self-elo 1100 \
  --engine-a-opponent-elo 1900 \
  --engine-a-temperature 0 \
  --engine-a-top-p 1 \
  --engine-b-path ~/chess/maia3-engine/maia3-engine.sh \
  --engine-b-name "Maia3 1900" \
  --engine-b-elo 1900 \
  --engine-b-self-elo 1900 \
  --engine-b-opponent-elo 1100 \
  --engine-b-temperature 0 \
  --engine-b-top-p 1 \
  --openings openings.pgn \
  --number-of-games 200 \
  --output maia3-1100-vs-1900.pgn
```

Opening books cannot be combined with `--openings`. Moves in the PGN suite are
the complete shared opening treatment; engine play begins after each prefix.

## Engine options

Every engine option has an A and B version:

- `--engine-a-path` / `--engine-b-path` — UCI launcher (required)
- `--engine-a-name` / `--engine-b-name` — label used in output and PGN
- `--engine-a-elo` / `--engine-b-elo` — Maia Elo setting
- `--engine-a-self-elo` / `--engine-b-self-elo` — engine SelfElo
- `--engine-a-opponent-elo` / `--engine-b-opponent-elo` — engine OppoElo
- `--engine-a-temperature` / `--engine-b-temperature` — Maia 3 Temperature
- `--engine-a-top-p` / `--engine-b-top-p` — Maia 3 TopP
- `--engine-a-book` / `--engine-b-book` — optional Polyglot book

Only specify options supported by the selected engine. Option names are matched
case-insensitively, so `ELO` and `Elo` are both handled.

For a cross-rating match, configure both self and opponent Elo on each engine.
For example, the 1100 profile should receive `SelfElo=1100` and
`OppoElo=1900`, while its opponent receives the reverse. The engine launcher
must expose those UCI options; the benchmark exits with a clear error if a
requested option is unavailable.

Match options:

- `--number-of-games` — even number of games (required)
- `--output` — PGN path; defaults to `benchmark-games.pgn`
- `--nodes` — nodes requested per move; defaults to `1`
- `--move-time-ms` — use a time limit per move instead of `--nodes`
- `--max-plies` — draw cutoff; defaults to `300`
- `--seed` — optional reproducible seed for opening-book choices
- `--openings` — PGN opening suite; every suite game is used for a reversed-color pair
- `--resume` — validate and continue an interrupted `--openings` match

Run `maia-benchmark --help` for the complete CLI reference.

## PGN opening suites

An opening suite is an ordinary PGN containing one or more games. The main line
of each game is treated as an opening prefix:

- every suite game must contain at least one legal move;
- the prefix must not already be terminal or reach `--max-plies`;
- standard starting positions and PGN `FEN`/`SetUp` positions are supported;
- PGN results and player names in the suite are not used;
- `--number-of-games` must be exactly twice the number of suite games.

For opening 1, Engine A plays White first and Engine B plays White second. The
same pattern repeats for every opening. Output games include `OpeningIndex`,
`OpeningSuite`, and `ConfigHash` headers so their schedule and configuration can
be audited.

Use one neutral suite for every matchup when comparing engine configurations.
Rating-specific books should not be used for that purpose because opening
quality would then be confounded with the engine setting being measured.

## Checkpointing and resume

Every completed game is written, flushed to disk, and announced immediately.
If a paired-opening match is interrupted, rerun the identical command with
`--resume`:

```bash
.venv/bin/maia-benchmark \
  ...same engine and match options... \
  --openings openings.pgn \
  --number-of-games 200 \
  --output maia3-1100-vs-1900.pgn \
  --resume
```

Before appending, the runner validates every completed game against the engine
labels, color schedule, opening index, opening moves, opening-suite SHA-256, and
all strength/search settings. It refuses to resume if the suite, engine paths,
ratings, sampling options, seed, limits, or requested game count changed.

Resume is intentionally limited to `--openings` matches, where the remaining
schedule is fully predetermined. Without `--resume`, the output file is started
from the beginning as in the original workflow.

## Published benchmark report

See the [expanded Maia 1600 engine-profile benchmark](reports/20260829_v1_maia_1600_benchmark/README.md)
for a worked example using this tool: five profiles, ten matchups, 1,000 games,
methodology, statistical analysis, performance observations, and the complete
PGN and game-level dataset. The original
[600-game report](reports/20260829_v0_maia_1600_benchmark/README.md) is preserved.

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
