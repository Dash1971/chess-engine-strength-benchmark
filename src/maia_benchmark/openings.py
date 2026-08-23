from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

import chess
import chess.polyglot

from .books import choose_move, validate_book
from .config import Experiment


@dataclass(frozen=True)
class Opening:
    id: int
    fen: str
    source_rating: int
    source_book_sha256: str
    prefix_uci: tuple[str, ...]


def generate_openings(exp: Experiment, output: Path) -> list[Opening]:
    cfg = exp.raw["openings"]
    ratings = tuple(int(v) for v in cfg["ratings"])
    min_plies, max_plies = int(cfg["min_plies"]), int(cfg["max_plies"])
    infos = {rating: validate_book(exp.book_path(rating)) for rating in ratings}
    readers = {rating: chess.polyglot.open_reader(info.path) for rating, info in infos.items()}
    rng = random.Random(exp.seed)
    openings: list[Opening] = []
    seen: set[str] = set()
    attempts = 0
    try:
        while len(openings) < exp.opening_pairs:
            attempts += 1
            if attempts > exp.opening_pairs * 200:
                raise RuntimeError("Could not generate enough unique opening positions")
            rating = ratings[len(openings) % len(ratings)]
            board = chess.Board()
            moves: list[str] = []
            target = rng.randint(min_plies, max_plies)
            for _ in range(target):
                move = choose_move(readers[rating], board, rng)
                if move is None or move not in board.legal_moves:
                    break
                moves.append(move.uci())
                board.push(move)
            position_key = chess.polyglot.zobrist_hash(board)
            if len(moves) < min_plies or board.is_game_over() or position_key in seen:
                continue
            seen.add(position_key)
            openings.append(
                Opening(len(openings), board.fen(), rating, infos[rating].sha256, tuple(moves))
            )
    finally:
        for reader in readers.values():
            reader.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for opening in openings:
            handle.write(json.dumps(asdict(opening), sort_keys=True) + "\n")
    return openings


def load_openings(path: Path) -> list[Opening]:
    result = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            row["prefix_uci"] = tuple(row["prefix_uci"])
            result.append(Opening(**row))
    return result
