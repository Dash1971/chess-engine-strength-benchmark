from __future__ import annotations

import sys
from pathlib import Path

import pytest

from maia_benchmark.gui import (
    build_command,
    format_duration,
    load_settings,
    progress_text,
    save_settings,
)


def base_values() -> dict[str, str]:
    return {
        "engine-a-path": "/tmp/a",
        "engine-a-name": "Engine A",
        "engine-a-book": "",
        "engine-b-path": "/tmp/b",
        "engine-b-name": "Engine B",
        "engine-b-book": "",
        "number-of-games": "2",
        "output": "/tmp/out.pgn",
        "openings": "/tmp/openings.pgn",
        "nodes": "1",
    }


def test_build_command_uses_current_interpreter_and_nonempty_values() -> None:
    command = build_command(base_values())

    assert command[:3] == [sys.executable, "-m", "maia_benchmark.cli"]
    assert command[command.index("--engine-a-name") + 1] == "Engine A"
    assert "--engine-a-book" not in command


def test_build_command_adds_resume() -> None:
    command = build_command(base_values(), resume=True)

    assert command[-1] == "--resume"


def test_build_command_rejects_books_with_opening_suite() -> None:
    values = base_values()
    values["engine-a-book"] = "/tmp/book.bin"

    with pytest.raises(ValueError, match="cannot be combined"):
        build_command(values)


def test_build_command_requires_openings_for_resume() -> None:
    values = base_values()
    values["openings"] = ""

    with pytest.raises(ValueError, match="Resume requires"):
        build_command(values, resume=True)


def test_build_command_reports_required_fields() -> None:
    values = base_values()
    values["engine-b-path"] = ""

    with pytest.raises(ValueError, match="engine b path"):
        build_command(values)


def test_settings_round_trip_strings_only(tmp_path: Path) -> None:
    path = tmp_path / "settings" / "gui-settings.json"
    save_settings(path, {"engine-a-path": "/engines/a", "nodes": "1"})

    assert load_settings(path) == {"engine-a-path": "/engines/a", "nodes": "1"}
    assert path.stat().st_mode & 0o777 == 0o600


def test_missing_or_invalid_settings_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "gui-settings.json"
    assert load_settings(path) == {}

    path.write_text("not json", encoding="utf-8")
    assert load_settings(path) == {}


def test_progress_text_includes_rate_and_eta() -> None:
    assert progress_text(25, 100, 900, 25) == (
        "Running — 25/100 games — elapsed 0:15:00 — 100.0 games/hour — ETA 0:45:00"
    )


def test_progress_text_uses_new_games_for_resumed_rate() -> None:
    assert progress_text(25, 100, 180, 5) == (
        "Running — 25/100 games — elapsed 0:03:00 — 100.0 games/hour — ETA 0:45:00"
    )


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "0:00:00"), (65, "0:01:05"), (3661, "1:01:01")],
)
def test_format_duration(seconds: float, expected: str) -> None:
    assert format_duration(seconds) == expected
