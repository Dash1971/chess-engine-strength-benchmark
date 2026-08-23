# chess-engine-strength-benchmark

A reproducible, statistically controlled round-robin benchmark comparing Maia 2
and Maia 3 ratings, opening-book modes, and Maia 3 sampling settings.

## Status

The experiment design and runner are under review. **No published result should
be treated as final until the complete run and its artifacts have been reviewed.**

## Design

The benchmark contains 21 profiles and 210 unordered matchups:

- Maia 2 at 1100, 1600, and 1900 Elo, book-enabled
- Maia 3 (`maia3-79m`) at those ratings, with and without books
- three Maia 3 policies:
  - argmax: Temperature 0, TopP 1
  - balanced: Temperature 0.5, TopP 0.9
  - maximum sampling: Temperature 1, TopP 1

Each matchup uses 500 opening positions, played twice with colors reversed, for
1,000 games and 210,000 games overall. The primary output is W/D/L and score
percentage with 95% confidence intervals.

### Opening controls

The runner—not the UCI wrappers—owns book selection. It validates every
Polyglot file before starting an engine, records whether every move came from
the book or model, and permanently switches a side to its model after its first
book miss.

- If both profiles are book-enabled, both use the higher Elo profile's Rapid
  book (1100 vs 1900 therefore uses the 1900 book for both).
- If only one profile is book-enabled, it uses its own rating book.
- No-book profiles never consult a Polyglot book after the common starting FEN.

A seeded, stratified suite of opening positions is required because deterministic
argmax profiles would otherwise replay the same start-position game. Every
opening is color-reversed. The generated suite records its FEN, move prefix,
source rating, and source-book checksum.

## Installation

Python 3.9 or newer is required.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
```

Set paths through environment variables; machine-local absolute paths are not
stored in the repository:

```bash
export MAIA2_ENGINE="$HOME/chess/maia2-engine/maia2-engine.sh"
export MAIA3_ENGINE="$HOME/chess/maia3-engine/maia3-engine.sh"
export MAIA_BOOK_DIR="$HOME/chess/books/Rapid/2026"
```

## Workflow

```bash
maia-benchmark validate
maia-benchmark build-openings
maia-benchmark schedule

# Smoke test one named matchup first. The run is resumable by game ID.
maia-benchmark run --matchup maia2-1100-book__vs__maia2-1600-book

maia-benchmark run --workers 4
maia-benchmark report
```

`--workers` parallelizes independent matchups. The throughput pilot determines
the safe value for the target Mac; `1` is the conservative default.

The full run must not begin until code review is complete, engine installation
is verified, and a throughput pilot has established a measured ETA and safe
concurrency on the target machine.

## Outputs

- one append-only JSONL file per matchup, resumable by game ID
- per-ply source provenance (`book` or `engine`)
- exact book-to-model transition ply for each side
- result and termination reason, including explicit maximum-ply cases
- aggregate CSV with both simple Wilson and opening-pair-clustered intervals
- annotated PGN reconstructed from the lossless JSONL records
- Markdown report

The manifest seed makes opening selection and book sampling reproducible. Maia
3's sampled policies are byte-for-byte reproducible only if the upstream UCI
engine exposes and honors a random-seed option; otherwise their aggregate
results are statistically reproducible, not identical move-for-move.

Raw results and generated artifacts are intentionally gitignored during local
runs. Approved releases will publish checksummed artifacts separately.

## License

Code in this repository is released under the MIT License. Maia model weights
retain their upstream licenses. Lichess database exports are CC0.
