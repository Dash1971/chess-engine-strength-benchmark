from __future__ import annotations

import sys

import pytest

from maia_benchmark.gui import build_command


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
