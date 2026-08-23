from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .config import Profile


@dataclass(frozen=True)
class Matchup:
    id: str
    a: Profile
    b: Profile


def matchups(profiles: list[Profile]) -> list[Matchup]:
    return [Matchup(f"{a.id}__vs__{b.id}", a, b) for a, b in combinations(profiles, 2)]

