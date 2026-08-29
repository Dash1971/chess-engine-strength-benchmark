from pathlib import Path

import chess
import chess.pgn
import pytest

from maia_benchmark.match import EngineConfig, MatchConfig, MatchRunner, MatchSummary


def engine(label: str = "Test") -> EngineConfig:
    return EngineConfig(label=label, path=Path(__file__))


def write_opening_suite(path: Path) -> None:
    game = chess.pgn.Game()
    node = game
    board = game.board()
    for uci in ("e2e4", "e7e5", "g1f3", "b8c6"):
        move = chess.Move.from_uci(uci)
        node = node.add_variation(move)
        board.push(move)
    path.write_text(f"{game}\n\n", encoding="utf-8")


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


def test_loads_pgn_opening_suite(tmp_path: Path) -> None:
    suite = tmp_path / "openings.pgn"
    write_opening_suite(suite)
    config = MatchConfig(engine(), engine("Other"), 2, tmp_path / "games.pgn", openings=suite)
    openings = MatchRunner(config)._load_openings()
    assert openings is not None
    assert len(openings) == 1
    assert [move.uci() for move in openings[0].moves] == [
        "e2e4",
        "e7e5",
        "g1f3",
        "b8c6",
    ]


def test_opening_suite_requires_exactly_two_games_per_opening(tmp_path: Path) -> None:
    suite = tmp_path / "openings.pgn"
    write_opening_suite(suite)
    config = MatchConfig(engine(), engine("Other"), 4, tmp_path / "games.pgn", openings=suite)
    with pytest.raises(ValueError, match="twice the number"):
        MatchRunner(config).run()


def test_opening_suite_cannot_be_combined_with_books(tmp_path: Path) -> None:
    suite = tmp_path / "openings.pgn"
    book = tmp_path / "book.bin"
    write_opening_suite(suite)
    book.touch()
    config = MatchConfig(
        EngineConfig("A", Path(__file__), book=book),
        engine("B"),
        2,
        tmp_path / "games.pgn",
        openings=suite,
    )
    with pytest.raises(ValueError, match="cannot be combined"):
        MatchRunner(config)._validate()


def test_resume_requires_openings(tmp_path: Path) -> None:
    config = MatchConfig(engine(), engine("Other"), 2, tmp_path / "games.pgn", resume=True)
    with pytest.raises(ValueError, match="requires --openings"):
        MatchRunner(config)._validate()


def test_resume_validates_hash_schedule_and_opening_prefix(tmp_path: Path) -> None:
    suite = tmp_path / "openings.pgn"
    output = tmp_path / "games.pgn"
    write_opening_suite(suite)
    config = MatchConfig(engine("A"), engine("B"), 2, output, openings=suite, resume=True)
    runner = MatchRunner(config)
    runner._validate()
    openings = runner._load_openings()
    assert openings is not None
    config_hash = runner._config_hash(runner._opening_digest())

    games = []
    for number, result in ((1, "1-0"), (2, "0-1")):
        game = chess.pgn.Game()
        game.headers.update(
            {
                "Round": str(number),
                "White": "A" if number == 1 else "B",
                "Black": "B" if number == 1 else "A",
                "Result": result,
                "ConfigHash": config_hash,
                "OpeningIndex": "1",
            }
        )
        node = game
        for move in openings[0].moves:
            node = node.add_variation(move)
        games.append(game)
    output.write_text("\n\n".join(str(game) for game in games) + "\n\n", encoding="utf-8")

    completed, wins, draws, losses = runner._resume_state(openings, config_hash)
    assert (completed, wins, draws, losses) == (2, 2, 0, 0)


def test_resume_rejects_changed_configuration(tmp_path: Path) -> None:
    suite = tmp_path / "openings.pgn"
    output = tmp_path / "games.pgn"
    write_opening_suite(suite)
    config = MatchConfig(engine("A"), engine("B"), 2, output, openings=suite, resume=True)
    runner = MatchRunner(config)
    openings = runner._load_openings()
    assert openings is not None
    game = chess.pgn.Game()
    game.headers.update(
        {
            "Round": "1",
            "White": "A",
            "Black": "B",
            "Result": "1-0",
            "ConfigHash": "wrong",
            "OpeningIndex": "1",
        }
    )
    node = game
    for move in openings[0].moves:
        node = node.add_variation(move)
    output.write_text(f"{game}\n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="ConfigHash"):
        runner._resume_state(openings, runner._config_hash(runner._opening_digest()))
