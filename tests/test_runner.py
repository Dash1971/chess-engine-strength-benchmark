import json
from pathlib import Path
from types import SimpleNamespace

import chess

from maia_benchmark.config import Experiment, Profile
from maia_benchmark.openings import Opening
from maia_benchmark.runner import _play_game, _repair_and_load_completed


class FirstLegalEngine:
    def play(self, board, limit, game=None):
        return SimpleNamespace(move=next(iter(board.legal_moves)))


class ScriptedEngine:
    def __init__(self, moves):
        self.moves = iter(moves)

    def play(self, board, limit, game=None):
        return SimpleNamespace(move=chess.Move.from_uci(next(self.moves)))


def opening(prefix=()):
    board = chess.Board()
    for move in prefix:
        board.push_uci(move)
    return Opening(1, board.fen(), 1100, "abc", tuple(prefix))


def experiment(tmp_path: Path, max_plies=4):
    return Experiment(tmp_path / "config.toml", {"seed": 7, "max_plies": max_plies})


def profiles():
    return (
        Profile("a", "maia2", 1100, False, None),
        Profile("b", "maia2", 1600, False, None),
    )


def test_maximum_ply_is_scored_as_draw(tmp_path: Path):
    a, b = profiles()
    row = _play_game(
        experiment(tmp_path), "game", opening(), a, b,
        FirstLegalEngine(), FirstLegalEngine(), None, None, {},
    )
    assert row["result"] == "1/2-1/2"
    assert row["termination"] == "max_plies"
    assert row["plies"] == 4
    assert "moves_uci" not in row


def test_game_decided_on_final_ply_keeps_real_termination(tmp_path: Path):
    a, b = profiles()
    white = ScriptedEngine(["f2f3", "g2g4"])
    black = ScriptedEngine(["e7e5", "d8h4"])
    row = _play_game(
        experiment(tmp_path), "mate", opening(), a, b, white, black, None, None, {},
        record_moves=True,
    )
    assert row["result"] == "0-1"
    assert row["termination"] == "checkmate"
    assert row["moves_uci"] == ["f2f3", "e7e5", "g2g4", "d8h4"]


def test_prefix_is_replayed_and_checked(tmp_path: Path):
    a, b = profiles()
    row = _play_game(
        experiment(tmp_path, max_plies=1), "prefix", opening(("e2e4",)), a, b,
        FirstLegalEngine(), FirstLegalEngine(), None, None, {},
    )
    assert row["plies"] == 1


def test_resume_repairs_truncated_final_line(tmp_path: Path):
    path = tmp_path / "results.jsonl"
    good = json.dumps({"game_id": "one"}) + "\n"
    path.write_bytes(good.encode() + b'{"game_id":"two"')
    assert _repair_and_load_completed(path) == {"one"}
    assert path.read_text() == good
