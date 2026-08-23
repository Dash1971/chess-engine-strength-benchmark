from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9/3.10
    import tomli as tomllib


@dataclass(frozen=True)
class Sampling:
    name: str
    temperature: float
    top_p: float


@dataclass(frozen=True)
class Profile:
    id: str
    family: str
    rating: int
    book_enabled: bool
    sampling: Sampling | None


@dataclass(frozen=True)
class Experiment:
    path: Path
    raw: dict[str, Any]

    @property
    def ratings(self) -> tuple[int, ...]:
        return tuple(self.raw["ratings"])

    @property
    def seed(self) -> int:
        return int(self.raw["seed"])

    @property
    def games_per_matchup(self) -> int:
        return int(self.raw["games_per_matchup"])

    @property
    def opening_pairs(self) -> int:
        return int(self.raw["opening_pairs"])

    @property
    def max_plies(self) -> int:
        return int(self.raw["max_plies"])

    def command(self, family: str) -> str:
        env_name = self.raw["engines"][family]["command_env"]
        value = os.environ.get(env_name)
        if not value:
            raise ValueError(f"Required environment variable {env_name} is not set")
        return value

    def book_dir(self) -> Path:
        env_name = self.raw["books"]["directory_env"]
        value = os.environ.get(env_name)
        if not value:
            raise ValueError(f"Required environment variable {env_name} is not set")
        return Path(value).expanduser().resolve()

    def book_path(self, rating: int) -> Path:
        template = self.raw["books"]["filename_template"]
        return self.book_dir() / template.format(rating=rating)

    def digest(self) -> str:
        return hashlib.sha256(self.path.read_bytes()).hexdigest()


def load_experiment(path: str | Path) -> Experiment:
    resolved = Path(path).resolve()
    with resolved.open("rb") as handle:
        raw = tomllib.load(handle)
    exp = Experiment(resolved, raw)
    validate_config(exp)
    return exp


def validate_config(exp: Experiment) -> None:
    if exp.raw.get("config_schema") != 1:
        raise ValueError("Unsupported experiment schema")
    if exp.games_per_matchup != exp.opening_pairs * 2:
        raise ValueError("games_per_matchup must equal opening_pairs * 2 for color reversal")
    if sorted(set(exp.ratings)) != list(exp.ratings):
        raise ValueError("ratings must be unique and sorted")
    for name, values in exp.raw["sampling"].items():
        temperature = float(values["temperature"])
        top_p = float(values["top_p"])
        if temperature < 0 or not 0 < top_p <= 1:
            raise ValueError(f"Invalid sampling configuration: {name}")


def profiles(exp: Experiment) -> list[Profile]:
    result: list[Profile] = []
    for rating in exp.ratings:
        result.append(Profile(f"maia2-{rating}-book", "maia2", rating, True, None))
    samplings = [
        Sampling(name, float(v["temperature"]), float(v["top_p"]))
        for name, v in exp.raw["sampling"].items()
    ]
    for rating in exp.ratings:
        for book_enabled in (True, False):
            book_name = "book" if book_enabled else "nobook"
            for sampling in samplings:
                profile_id = f"maia3-{rating}-{book_name}-{sampling.name}"
                result.append(Profile(profile_id, "maia3", rating, book_enabled, sampling))
    return result
