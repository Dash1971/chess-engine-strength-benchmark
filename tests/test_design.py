from pathlib import Path

from maia_benchmark.books import matchup_book_rating
from maia_benchmark.config import load_experiment, profiles
from maia_benchmark.report import paired_interval, wilson
from maia_benchmark.schedule import matchups

CONFIG = Path(__file__).parents[1] / "config" / "experiment.toml"


def test_profile_and_matchup_counts():
    exp = load_experiment(CONFIG)
    configured = profiles(exp)
    assert len(configured) == 21
    assert len(matchups(configured)) == 210
    assert len(matchups(configured)) * exp.games_per_matchup == 210_000


def test_higher_rating_book_rule():
    assert matchup_book_rating(1100, 1900) == 1900
    assert matchup_book_rating(1600, 1100) == 1600
    assert matchup_book_rating(1600, 1600) == 1600


def test_wilson_interval_at_half_score():
    low, high = wilson(500, 1000)
    assert round(100 * (high - 0.5), 1) == 3.1
    assert round(100 * (0.5 - low), 1) == 3.1


def test_paired_interval_clusters_color_reversals():
    low, high = paired_interval([0.0, 0.5, 1.0])
    assert low == 0.0
    assert high == 1.0
