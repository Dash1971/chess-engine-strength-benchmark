from pathlib import Path
from types import SimpleNamespace

import chess

from maia_benchmark.config import Experiment, Profile
from maia_benchmark.openings import Opening
from maia_benchmark.runner import _play_game


class FirstLegalEngine:
    def play(self, board, limit, game=None):
        return SimpleNamespace(move=next(iter(board.legal_moves)))


def test_game_records_compact_result_without_per_move_data(tmp_path: Path):
    exp = Experiment(
        tmp_path / "config.toml",
        {"seed": 7, "max_plies": 4},
    )
    profile_a = Profile("a", "maia2", 1100, False, None)
    profile_b = Profile("b", "maia2", 1600, False, None)
    row = _play_game(
        exp,
        "a__vs__b:opening-0001:0",
        Opening("opening-0001", chess.STARTING_FEN, [], 1100, "abc"),
        profile_a,
        profile_b,
        FirstLegalEngine(),
        FirstLegalEngine(),
        None,
        None,
        {},
    )
    assert row["termination"] == "max_plies"
    assert row["plies"] == 4
    assert "moves" not in row
    assert "source_counts" not in row
    assert "transitions" not in row
