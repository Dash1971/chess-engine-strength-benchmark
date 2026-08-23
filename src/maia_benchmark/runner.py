from __future__ import annotations

import json
import random
import shlex
from pathlib import Path

import chess
import chess.engine
import chess.polyglot

from .books import choose_move, matchup_book_rating
from .config import Experiment, Profile
from .openings import Opening
from .schedule import Matchup


def _configure(engine: chess.engine.SimpleEngine, profile: Profile) -> None:
    if profile.family == "maia2":
        engine.configure({"ELO": profile.rating, "HumanTime": False, "BookFile": ""})
    else:
        assert profile.sampling is not None
        engine.configure(
            {
                "Elo": profile.rating,
                "SelfElo": profile.rating,
                "OppoElo": profile.rating,
                "Temperature": profile.sampling.temperature,
                "TopP": profile.sampling.top_p,
                "HumanTime": False,
                "BookFile": "",
            }
        )


def _book_paths(exp: Experiment, a: Profile, b: Profile) -> tuple[Path | None, Path | None]:
    if a.book_enabled and b.book_enabled:
        shared = exp.book_path(matchup_book_rating(a.rating, b.rating))
        return shared, shared
    return (exp.book_path(a.rating) if a.book_enabled else None,
            exp.book_path(b.rating) if b.book_enabled else None)


def run_matchup(
    exp: Experiment,
    matchup: Matchup,
    openings: list[Opening],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{matchup.id}.jsonl"
    completed: set[str] = set()
    if output.exists():
        with output.open(encoding="utf-8") as handle:
            completed = {json.loads(line)["game_id"] for line in handle if line.strip()}

    a_book, b_book = _book_paths(exp, matchup.a, matchup.b)
    readers = {
        path: chess.polyglot.open_reader(path) for path in {a_book, b_book} - {None}
    }
    a_engine = chess.engine.SimpleEngine.popen_uci(shlex.split(exp.command(matchup.a.family)))
    b_engine = chess.engine.SimpleEngine.popen_uci(shlex.split(exp.command(matchup.b.family)))
    try:
        _configure(a_engine, matchup.a)
        _configure(b_engine, matchup.b)
        for opening in openings:
            for reversal in (0, 1):
                game_id = f"{matchup.id}:{opening.id}:{reversal}"
                if game_id in completed:
                    continue
                white_profile, black_profile = (
                    (matchup.a, matchup.b) if reversal == 0 else (matchup.b, matchup.a)
                )
                white_engine, black_engine = (
                    (a_engine, b_engine) if reversal == 0 else (b_engine, a_engine)
                )
                white_book, black_book = (
                    (a_book, b_book) if reversal == 0 else (b_book, a_book)
                )
                row = _play_game(
                    exp, game_id, opening, white_profile, black_profile,
                    white_engine, black_engine, white_book, black_book, readers,
                )
                with output.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
    finally:
        a_engine.quit()
        b_engine.quit()
        for reader in readers.values():
            reader.close()
    return output


def _play_game(
    exp: Experiment,
    game_id: str,
    opening: Opening,
    white_profile: Profile,
    black_profile: Profile,
    white_engine: chess.engine.SimpleEngine,
    black_engine: chess.engine.SimpleEngine,
    white_book: Path | None,
    black_book: Path | None,
    readers: dict[Path, chess.polyglot.MemoryMappedReader],
) -> dict:
    board = chess.Board(opening.fen)
    rng = random.Random(f"{exp.seed}:{game_id}")
    book_active = {chess.WHITE: white_book is not None, chess.BLACK: black_book is not None}
    plies = 0
    termination = None
    for _ in range(exp.max_plies):
        if board.is_game_over(claim_draw=True):
            break
        color = board.turn
        profile = white_profile if color == chess.WHITE else black_profile
        engine = white_engine if color == chess.WHITE else black_engine
        book_path = white_book if color == chess.WHITE else black_book
        move = None
        if book_active[color] and book_path is not None:
            move = choose_move(readers[book_path], board, rng)
            if move is None:
                book_active[color] = False
        if move is None:
            result = engine.play(board, chess.engine.Limit(nodes=1), game=game_id)
            move = result.move
        if move not in board.legal_moves:
            raise RuntimeError(f"Illegal move {move} from {profile.id} in {game_id}")
        board.push(move)
        plies += 1
    else:
        termination = "max_plies"

    outcome = board.outcome(claim_draw=True)
    result = outcome.result() if outcome else "*"
    if termination is None:
        termination = outcome.termination.name.lower() if outcome else "unknown"
    return {
        "schema_version": 2,
        "game_id": game_id,
        "opening_id": opening.id,
        "white": white_profile.id,
        "black": black_profile.id,
        "result": result,
        "termination": termination,
        "plies": plies,
    }
