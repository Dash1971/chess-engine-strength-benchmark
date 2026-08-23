from pathlib import Path

from maia_benchmark.config import Experiment, Profile, load_experiment, profiles
from maia_benchmark.report import paired_interval, wilson
from maia_benchmark.runner import _book_paths
from maia_benchmark.schedule import matchups

CONFIG = Path(__file__).parents[1] / "config" / "experiment.toml"


def test_profile_and_matchup_counts():
    exp = load_experiment(CONFIG)
    configured = profiles(exp)
    assert len(configured) == 21
    assert len(matchups(configured)) == 210
    assert len(matchups(configured)) * exp.games_per_matchup == 210_000


def test_each_booked_profile_uses_its_own_rating_book(tmp_path, monkeypatch):
    monkeypatch.setenv("MAIA_BOOK_DIR", str(tmp_path))
    exp = Experiment(
        tmp_path / "config.toml",
        {
            "books": {
                "directory_env": "MAIA_BOOK_DIR",
                "filename_template": "rapid-{rating}.bin",
            }
        },
    )
    maia2 = Profile("maia2-1900-book", "maia2", 1900, True, None)
    maia3 = Profile("maia3-1600-book", "maia3", 1600, True, None)
    a_book, b_book = _book_paths(exp, maia2, maia3)
    assert a_book == tmp_path / "rapid-1900.bin"
    assert b_book == tmp_path / "rapid-1600.bin"


def test_wilson_interval_at_half_score():
    low, high = wilson(500, 1000)
    assert round(100 * (high - 0.5), 1) == 3.1
    assert round(100 * (0.5 - low), 1) == 3.1


def test_paired_interval_clusters_color_reversals():
    low, high = paired_interval([0.0, 0.5, 1.0])
    assert low == 0.0
    assert high == 1.0
