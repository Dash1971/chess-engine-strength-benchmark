from __future__ import annotations

import hashlib
import random
import struct
from dataclasses import dataclass
from pathlib import Path

import chess
import chess.polyglot

ENTRY = struct.Struct(">QHHI")


@dataclass(frozen=True)
class BookInfo:
    path: Path
    size: int
    entries: int
    sha256: str


def validate_book(path: Path) -> BookInfo:
    if not path.is_file():
        raise ValueError(f"Opening book not found: {path}")
    size = path.stat().st_size
    if size == 0 or size % ENTRY.size:
        raise ValueError(f"Invalid Polyglot size: {path} ({size} bytes)")
    previous = -1
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            for offset in range(0, len(chunk) - ENTRY.size + 1, ENTRY.size):
                key = ENTRY.unpack_from(chunk, offset)[0]
                if key < previous:
                    raise ValueError(f"Unsorted Polyglot book: {path}")
                previous = key
    return BookInfo(path.resolve(), size, size // ENTRY.size, digest.hexdigest())


def choose_move(reader: chess.polyglot.MemoryMappedReader, board: chess.Board, rng: random.Random):
    entries = list(reader.find_all(board))
    if not entries:
        return None
    weights = [max(0, entry.weight) for entry in entries]
    if not any(weights):
        return rng.choice(entries).move
    return rng.choices([entry.move for entry in entries], weights=weights, k=1)[0]


def matchup_book_rating(a_rating: int, b_rating: int) -> int:
    """Both booked engines use the higher Elo book."""
    return max(a_rating, b_rating)

