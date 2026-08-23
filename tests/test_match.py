from pathlib import Path

import pytest

from maia_benchmark.match import EngineConfig, MatchConfig, MatchRunner, MatchSummary


def engine(label: str = "Test") -> EngineConfig:
    return EngineConfig(label=label, path=Path(__file__))


def test_summary_percentages() -> None:
    summary = MatchSummary(3, 4, 3, 1.0, Path("games.pgn"))
    assert summary.win_percentage == 30.0
    assert summary.score_percentage == 50.0


@pytest.mark.parametrize("games", [0, 1, 3, 99])
def test_game_count_must_be_even(games: int) -> None:
    config = MatchConfig(engine(), engine("Other"), games, Path("games.pgn"))
    with pytest.raises(ValueError, match="even number"):
        MatchRunner(config)._validate()


def test_validates_temperature_and_top_p() -> None:
    bad_temperature = EngineConfig("A", Path(__file__), temperature=-0.1)
    bad_top_p = EngineConfig("B", Path(__file__), top_p=0)
    with pytest.raises(ValueError, match="Temperature"):
        MatchRunner(MatchConfig(bad_temperature, engine(), 2, Path("games.pgn")))._validate()
    with pytest.raises(ValueError, match="TopP"):
        MatchRunner(MatchConfig(engine(), bad_top_p, 2, Path("games.pgn")))._validate()
