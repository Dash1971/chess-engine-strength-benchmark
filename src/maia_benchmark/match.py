from __future__ import annotations

import hashlib
import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine
import chess.pgn
import chess.polyglot


@dataclass(frozen=True)
class EngineConfig:
    label: str
    path: Path
    elo: int | None = None
    self_elo: int | None = None
    opponent_elo: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    book: Path | None = None


@dataclass(frozen=True)
class MatchConfig:
    engine_a: EngineConfig
    engine_b: EngineConfig
    number_of_games: int
    output: Path
    nodes: int = 1
    move_time_ms: int | None = None
    max_plies: int = 300
    seed: int | None = None
    openings: Path | None = None
    resume: bool = False


@dataclass(frozen=True)
class Opening:
    initial_fen: str
    moves: tuple[chess.Move, ...]


@dataclass(frozen=True)
class MatchSummary:
    engine_a_wins: int
    draws: int
    engine_a_losses: int
    elapsed_seconds: float
    output: Path

    @property
    def games(self) -> int:
        return self.engine_a_wins + self.draws + self.engine_a_losses

    @property
    def win_percentage(self) -> float:
        return self.engine_a_wins / self.games * 100

    @property
    def score_percentage(self) -> float:
        return (self.engine_a_wins + self.draws / 2) / self.games * 100


class MatchRunner:
    def __init__(self, config: MatchConfig):
        self.config = config
        self.rng = random.Random(config.seed)

    def run(self) -> MatchSummary:
        self._validate()
        openings = self._load_openings()
        if openings is not None and self.config.number_of_games != len(openings) * 2:
            raise ValueError(
                "--number-of-games must equal twice the number of opening-suite games "
                f"({len(openings) * 2})"
            )
        opening_digest = self._opening_digest()
        config_hash = self._config_hash(opening_digest)
        self.config.output.parent.mkdir(parents=True, exist_ok=True)
        completed_games, wins, draws, losses = self._resume_state(openings, config_hash)
        if completed_games == self.config.number_of_games:
            return MatchSummary(wins, draws, losses, 0.0, self.config.output)
        readers = self._open_books()
        a_engine: chess.engine.SimpleEngine | None = None
        b_engine: chess.engine.SimpleEngine | None = None
        started = time.perf_counter()
        try:
            a_engine = chess.engine.SimpleEngine.popen_uci(str(self.config.engine_a.path))
            b_engine = chess.engine.SimpleEngine.popen_uci(str(self.config.engine_b.path))
            self._configure(a_engine, self.config.engine_a)
            self._configure(b_engine, self.config.engine_b)
            mode = "a" if completed_games else "w"
            with self.config.output.open(mode, encoding="utf-8") as pgn_file:
                for game_number in range(completed_games + 1, self.config.number_of_games + 1):
                    a_is_white = game_number % 2 == 1
                    opening = openings[(game_number - 1) // 2] if openings is not None else None
                    game = self._play_game(
                        a_engine,
                        b_engine,
                        readers,
                        a_is_white,
                        game_number,
                        opening,
                        config_hash,
                    )
                    print(game, file=pgn_file, end="\n\n")
                    pgn_file.flush()
                    os.fsync(pgn_file.fileno())
                    result = game.headers["Result"]
                    if result == "1/2-1/2":
                        draws += 1
                    elif (result == "1-0") == a_is_white:
                        wins += 1
                    else:
                        losses += 1
                    print(
                        f"Game {game_number}/{self.config.number_of_games}: {result} "
                        f"({game.headers['White']} vs {game.headers['Black']})",
                        flush=True,
                    )
        finally:
            for reader in readers.values():
                reader.close()
            if a_engine is not None:
                self._quit(a_engine)
            if b_engine is not None:
                self._quit(b_engine)
        return MatchSummary(wins, draws, losses, time.perf_counter() - started, self.config.output)

    def _validate(self) -> None:
        if self.config.number_of_games < 2 or self.config.number_of_games % 2:
            raise ValueError("--number-of-games must be an even number of at least 2")
        if self.config.nodes < 1:
            raise ValueError("--nodes must be at least 1")
        if self.config.move_time_ms is not None and self.config.move_time_ms < 1:
            raise ValueError("--move-time-ms must be at least 1")
        if self.config.max_plies < 1:
            raise ValueError("--max-plies must be at least 1")
        if self.config.openings is not None:
            if not self.config.openings.expanduser().is_file():
                raise ValueError(f"Opening suite not found: {self.config.openings}")
            if any(engine.book is not None for engine in (self.config.engine_a, self.config.engine_b)):
                raise ValueError("--openings cannot be combined with engine opening books")
        if self.config.resume and self.config.openings is None:
            raise ValueError("--resume requires --openings")
        for engine in (self.config.engine_a, self.config.engine_b):
            if not engine.path.expanduser().is_file():
                raise ValueError(f"Engine not found: {engine.path}")
            if engine.temperature is not None and engine.temperature < 0:
                raise ValueError(f"{engine.label}: Temperature must be at least 0")
            if engine.top_p is not None and not 0 < engine.top_p <= 1:
                raise ValueError(f"{engine.label}: TopP must be greater than 0 and at most 1")
            if engine.book is not None and not engine.book.expanduser().is_file():
                raise ValueError(f"Opening book not found: {engine.book}")

    def _open_books(self) -> dict[Path, chess.polyglot.MemoryMappedReader]:
        paths = {
            engine.book.expanduser().resolve()
            for engine in (self.config.engine_a, self.config.engine_b)
            if engine.book is not None
        }
        return {path: chess.polyglot.open_reader(path) for path in paths}

    @staticmethod
    def _option_name(engine: chess.engine.SimpleEngine, requested: str) -> str:
        matches = [name for name in engine.options if name.lower() == requested.lower()]
        if not matches:
            raise ValueError(f"{engine.id.get('name', '<unknown>')} has no {requested} option")
        return matches[0]

    def _configure(self, engine: chess.engine.SimpleEngine, config: EngineConfig) -> None:
        requested = {
            "Elo": config.elo,
            "SelfElo": config.self_elo,
            "OppoElo": config.opponent_elo,
            "Temperature": config.temperature,
            "TopP": config.top_p,
        }
        options = {
            self._option_name(engine, name): value
            for name, value in requested.items()
            if value is not None
        }
        threads = [name for name in engine.options if name.lower() == "threads"]
        if threads:
            options[threads[0]] = 1
        if options:
            engine.configure(options)

    def _play_game(
        self,
        a_engine: chess.engine.SimpleEngine,
        b_engine: chess.engine.SimpleEngine,
        readers: dict[Path, chess.polyglot.MemoryMappedReader],
        a_is_white: bool,
        game_number: int,
        opening: Opening | None = None,
        config_hash: str = "",
    ) -> chess.pgn.Game:
        white_config, black_config = (
            (self.config.engine_a, self.config.engine_b)
            if a_is_white
            else (self.config.engine_b, self.config.engine_a)
        )
        white_engine, black_engine = (a_engine, b_engine) if a_is_white else (b_engine, a_engine)
        board = chess.Board(opening.initial_fen) if opening is not None else chess.Board()
        game = chess.pgn.Game()
        if opening is not None and opening.initial_fen != chess.STARTING_FEN:
            game.setup(board)
        game.headers.update(
            {
                "Event": "Engine benchmark",
                "Round": str(game_number),
                "White": white_config.label,
                "Black": black_config.label,
                "ConfigHash": config_hash,
            }
        )
        if opening is not None:
            game.headers["OpeningIndex"] = str((game_number + 1) // 2)
            game.headers["OpeningSuite"] = self.config.openings.name
        if white_config.elo is not None:
            game.headers["WhiteElo"] = str(white_config.elo)
        if black_config.elo is not None:
            game.headers["BlackElo"] = str(black_config.elo)
        node = game
        if opening is not None:
            for move in opening.moves:
                if move not in board.legal_moves:
                    raise RuntimeError(f"Illegal move {move} in opening {game.headers['OpeningIndex']}")
                board.push(move)
                node = node.add_variation(move)
        book_active = {chess.WHITE: white_config.book is not None, chess.BLACK: black_config.book is not None}
        for _ in range(board.ply(), self.config.max_plies):
            if board.is_game_over(claim_draw=True):
                break
            color = board.turn
            engine_config = white_config if color == chess.WHITE else black_config
            engine = white_engine if color == chess.WHITE else black_engine
            move = self._book_move(engine_config, board, readers) if book_active[color] else None
            if move is None:
                book_active[color] = False
                limit = (
                    chess.engine.Limit(time=self.config.move_time_ms / 1000)
                    if self.config.move_time_ms is not None
                    else chess.engine.Limit(nodes=self.config.nodes)
                )
                move = engine.play(board, limit, game=f"benchmark-{game_number}").move
            if move not in board.legal_moves:
                raise RuntimeError(f"Illegal move {move} from {engine_config.label}")
            board.push(move)
            node = node.add_variation(move)
        outcome = board.outcome(claim_draw=True)
        if outcome is None:
            result, termination = "1/2-1/2", "max plies"
        else:
            result = outcome.result()
            termination = outcome.termination.name.lower().replace("_", " ")
        game.headers["Result"] = result
        game.headers["Termination"] = termination
        return game

    def _load_openings(self) -> list[Opening] | None:
        if self.config.openings is None:
            return None
        openings: list[Opening] = []
        with self.config.openings.expanduser().open(encoding="utf-8") as handle:
            while game := chess.pgn.read_game(handle):
                if game.errors:
                    raise ValueError(f"Invalid opening suite PGN: {game.errors[0]}")
                board = game.board()
                initial_fen = board.fen()
                moves = tuple(game.mainline_moves())
                if not moves:
                    raise ValueError("Every opening-suite game must contain at least one move")
                for move in moves:
                    if move not in board.legal_moves:
                        raise ValueError(f"Illegal move {move} in opening-suite game {len(openings) + 1}")
                    board.push(move)
                if board.is_game_over(claim_draw=True):
                    raise ValueError(f"Opening-suite game {len(openings) + 1} is already terminal")
                if board.ply() >= self.config.max_plies:
                    raise ValueError(
                        f"Opening-suite game {len(openings) + 1} reaches --max-plies"
                    )
                openings.append(Opening(initial_fen, moves))
        if not openings:
            raise ValueError("Opening suite contains no games")
        return openings

    def _opening_digest(self) -> str | None:
        if self.config.openings is None:
            return None
        return hashlib.sha256(self.config.openings.expanduser().read_bytes()).hexdigest()

    def _config_hash(self, opening_digest: str | None) -> str:
        def engine_values(engine: EngineConfig) -> dict[str, object]:
            return {
                "label": engine.label,
                "path": str(engine.path.expanduser().resolve()),
                "elo": engine.elo,
                "self_elo": engine.self_elo,
                "opponent_elo": engine.opponent_elo,
                "temperature": engine.temperature,
                "top_p": engine.top_p,
                "book": str(engine.book.expanduser().resolve()) if engine.book else None,
            }

        values = {
            "engine_a": engine_values(self.config.engine_a),
            "engine_b": engine_values(self.config.engine_b),
            "number_of_games": self.config.number_of_games,
            "nodes": self.config.nodes,
            "move_time_ms": self.config.move_time_ms,
            "max_plies": self.config.max_plies,
            "seed": self.config.seed,
            "opening_sha256": opening_digest,
        }
        encoded = json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _resume_state(
        self, openings: list[Opening] | None, config_hash: str
    ) -> tuple[int, int, int, int]:
        if not self.config.resume or not self.config.output.exists():
            return 0, 0, 0, 0
        completed = wins = draws = losses = 0
        with self.config.output.open(encoding="utf-8") as handle:
            while game := chess.pgn.read_game(handle):
                completed += 1
                if completed > self.config.number_of_games:
                    raise ValueError("Resume PGN contains more games than requested")
                if game.errors:
                    raise ValueError(f"Invalid resume PGN: {game.errors[0]}")
                self._validate_resumed_game(game, completed, openings, config_hash)
                result = game.headers["Result"]
                a_is_white = completed % 2 == 1
                if result == "1/2-1/2":
                    draws += 1
                elif (result == "1-0") == a_is_white:
                    wins += 1
                else:
                    losses += 1
        return completed, wins, draws, losses

    def _validate_resumed_game(
        self,
        game: chess.pgn.Game,
        game_number: int,
        openings: list[Opening] | None,
        config_hash: str,
    ) -> None:
        a_is_white = game_number % 2 == 1
        expected_white, expected_black = (
            (self.config.engine_a.label, self.config.engine_b.label)
            if a_is_white
            else (self.config.engine_b.label, self.config.engine_a.label)
        )
        expected = {
            "Round": str(game_number),
            "White": expected_white,
            "Black": expected_black,
            "ConfigHash": config_hash,
            "OpeningIndex": str((game_number + 1) // 2),
        }
        for name, value in expected.items():
            if game.headers.get(name) != value:
                raise ValueError(
                    f"Resume PGN game {game_number} has incompatible {name}: "
                    f"expected {value!r}, found {game.headers.get(name)!r}"
                )
        if game.headers.get("Result") not in {"1-0", "0-1", "1/2-1/2"}:
            raise ValueError(f"Resume PGN game {game_number} has no resolved result")
        if openings is None:
            raise ValueError("Resume requires an opening suite")
        opening = openings[(game_number - 1) // 2]
        if game.board().fen() != opening.initial_fen:
            raise ValueError(f"Resume PGN game {game_number} has the wrong initial position")
        actual_moves = tuple(game.mainline_moves())
        if actual_moves[: len(opening.moves)] != opening.moves:
            raise ValueError(f"Resume PGN game {game_number} has the wrong opening prefix")

    def _book_move(
        self,
        config: EngineConfig,
        board: chess.Board,
        readers: dict[Path, chess.polyglot.MemoryMappedReader],
    ) -> chess.Move | None:
        if config.book is None:
            return None
        entries = list(readers[config.book.expanduser().resolve()].find_all(board))
        if not entries:
            return None
        weights = [entry.weight for entry in entries]
        entry = self.rng.choices(entries, weights=weights, k=1)[0] if any(weights) else self.rng.choice(entries)
        return entry.move

    @staticmethod
    def _quit(engine: chess.engine.SimpleEngine) -> None:
        try:
            engine.quit()
        except (chess.engine.EngineError, OSError, TimeoutError):
            engine.close()
