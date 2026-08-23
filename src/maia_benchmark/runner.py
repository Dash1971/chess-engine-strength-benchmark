from __future__ import annotations

import hashlib
import json
import random
import shlex
import shutil
import time
from pathlib import Path

import chess
import chess.engine
import chess.polyglot

from .books import choose_move
from .config import Experiment, Profile
from .openings import Opening
from .schedule import Matchup


def validate_engine(exp: Experiment, profile: Profile) -> dict:
    command = shlex.split(exp.command(profile.family))
    executable = shutil.which(command[0]) or command[0]
    executable_path = Path(executable).resolve()
    if not executable_path.is_file():
        raise ValueError(f"Engine executable not found: {executable_path}")
    digest = hashlib.sha256(executable_path.read_bytes()).hexdigest()
    engine = chess.engine.SimpleEngine.popen_uci(command)
    try:
        _configure(engine, profile)
        board = chess.Board()
        played = engine.play(board, chess.engine.Limit(nodes=1), game="validation-probe")
        if played.move not in board.legal_moves:
            raise RuntimeError(f"Engine returned illegal validation move: {played.move}")
        return {
            "family": profile.family,
            "id": dict(engine.id),
            "binary_sha256": digest,
            "options": sorted(engine.options),
            "probe_move": played.move.uci(),
            "probe_nodes": played.info.get("nodes"),
        }
    finally:
        engine.close()


def _option_name(engine: chess.engine.SimpleEngine, requested: str) -> str:
    matches = [name for name in engine.options if name.lower() == requested.lower()]
    if not matches:
        raise ValueError(f"Engine {engine.id.get('name', '<unknown>')} lacks UCI option {requested}")
    return matches[0]


def _configure(engine: chess.engine.SimpleEngine, profile: Profile) -> None:
    if profile.family == "maia2":
        requested = {"ELO": profile.rating, "HumanTime": False, "BookFile": ""}
    else:
        assert profile.sampling is not None
        requested = {
            "Elo": profile.rating,
            "SelfElo": profile.rating,
            "OppoElo": profile.rating,
            "Temperature": profile.sampling.temperature,
            "TopP": profile.sampling.top_p,
        }
    configured = {_option_name(engine, name): value for name, value in requested.items()}
    threads = [name for name in engine.options if name.lower() == "threads"]
    if threads:
        configured[threads[0]] = 1
    engine.configure(configured)


def _book_paths(exp: Experiment, a: Profile, b: Profile) -> tuple[Path | None, Path | None]:
    return (
        exp.book_path(a.rating) if a.book_enabled else None,
        exp.book_path(b.rating) if b.book_enabled else None,
    )


def run_matchup(
    exp: Experiment,
    matchup: Matchup,
    openings: list[Opening],
    output_dir: Path,
    record_moves: bool = False,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{matchup.id}.jsonl"
    completed: set[str] = set()
    if output.exists():
        completed = _repair_and_load_completed(output)
    expected_games = len(openings) * 2
    if len(completed) == expected_games:
        return output
    starting_completed = len(completed)
    matchup_started = time.perf_counter()

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
                for attempt in range(2):
                    try:
                        row = _play_game(
                            exp, game_id, opening, white_profile, black_profile,
                            white_engine, black_engine, white_book, black_book, readers,
                            record_moves=record_moves,
                        )
                        break
                    except (chess.engine.EngineError, OSError, EOFError) as error:
                        _append_error(output_dir, matchup.id, game_id, attempt + 1, error)
                        a_engine.close()
                        b_engine.close()
                        if attempt:
                            raise
                        a_engine = chess.engine.SimpleEngine.popen_uci(
                            shlex.split(exp.command(matchup.a.family))
                        )
                        b_engine = chess.engine.SimpleEngine.popen_uci(
                            shlex.split(exp.command(matchup.b.family))
                        )
                        _configure(a_engine, matchup.a)
                        _configure(b_engine, matchup.b)
                        white_engine, black_engine = (
                            (a_engine, b_engine) if reversal == 0 else (b_engine, a_engine)
                        )
                with output.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
                completed.add(game_id)
                if len(completed) % 25 == 0 or len(completed) == expected_games:
                    _write_progress(
                        output_dir, matchup.id, len(completed), expected_games, matchup_started,
                        starting_completed,
                    )
    finally:
        a_engine.close()
        b_engine.close()
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
    record_moves: bool = False,
) -> dict:
    board = chess.Board()
    for uci in opening.prefix_uci:
        board.push_uci(uci)
    if board.fen() != opening.fen:
        raise ValueError(f"Opening prefix/FEN mismatch: {opening.id}")
    rng = random.Random(f"{exp.seed}:{game_id}")
    book_active = {chess.WHITE: white_book is not None, chess.BLACK: black_book is not None}
    book_exit = {chess.WHITE: None, chess.BLACK: None}
    moves: list[str] = []
    plies = 0
    started = time.perf_counter()
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
                book_exit[color] = plies + 1
        if move is None:
            result = engine.play(board, chess.engine.Limit(nodes=1), game=game_id)
            move = result.move
        if move not in board.legal_moves:
            raise RuntimeError(f"Illegal move {move} from {profile.id} in {game_id}")
        board.push(move)
        if record_moves:
            moves.append(move.uci())
        plies += 1

    outcome = board.outcome(claim_draw=True)
    if outcome is None:
        result = "1/2-1/2"
        termination = "max_plies"
    else:
        result = outcome.result()
        termination = outcome.termination.name.lower()
    row = {
        "record_schema": 3,
        "game_id": game_id,
        "opening_id": opening.id,
        "white": white_profile.id,
        "black": black_profile.id,
        "result": result,
        "termination": termination,
        "plies": plies,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "white_book_exit_ply": book_exit[chess.WHITE],
        "black_book_exit_ply": book_exit[chess.BLACK],
    }
    if record_moves:
        row["moves_uci"] = moves
    return row


def _repair_and_load_completed(path: Path) -> set[str]:
    completed: set[str] = set()
    last_good = 0
    with path.open("rb+") as handle:
        while True:
            line = handle.readline()
            if not line:
                break
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                handle.truncate(last_good)
                break
            completed.add(row["game_id"])
            last_good = handle.tell()
    return completed


def _append_error(
    output_dir: Path, matchup_id: str, game_id: str, attempt: int, error: Exception
) -> None:
    row = {
        "matchup": matchup_id,
        "game_id": game_id,
        "attempt": attempt,
        "error_type": type(error).__name__,
        "error": str(error),
        "timestamp": time.time(),
    }
    path = output_dir / f"{matchup_id}.errors.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_progress(
    output_dir: Path, matchup_id: str, completed: int, expected: int, started: float,
    starting_completed: int,
) -> None:
    elapsed = time.perf_counter() - started
    session_games = completed - starting_completed
    row = {
        "matchup": matchup_id,
        "completed": completed,
        "expected": expected,
        "elapsed_seconds_this_session": round(elapsed, 3),
        "games_per_hour_this_session": round(session_games / elapsed * 3600, 3),
        "updated_at": time.time(),
    }
    path = output_dir / f"{matchup_id}.progress.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)
