"""Deterministic, fairness-first round-robin scheduler (feature 8).

Given the teams available for a weekend and their historical matchups, produce
a set of pairings that:
  1. prioritises pairs who have met the *fewest* times (even chances),
  2. rotates grounds so no team always plays at the same venue,
  3. respects one match per team per slot.

Azure OpenAI is used only to *explain* / summarise the output (see ai.py); the
pairing itself is deterministic and auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Optional


@dataclass
class Pairing:
    home_team_id: str
    away_team_id: str
    ground_id: Optional[str]
    meetings_so_far: int


@dataclass
class ScheduleResult:
    pairings: list[Pairing] = field(default_factory=list)
    byes: list[str] = field(default_factory=list)
    fairness_score: float = 0.0   # lower = fairer (variance of matchup counts)


def build_round_robin(
    team_ids: list[str],
    head_to_head: dict[tuple[str, str], int],
    grounds: list[str],
    home_ground: dict[str, str] | None = None,
    avoid_pairs: set | None = None,
    team_grounds: dict[str, set] | None = None,
) -> ScheduleResult:
    """Greedy min-cost matching on this weekend's available teams.

    head_to_head: symmetric counts keyed by sorted (a, b) tuple.
    avoid_pairs: sorted (a,b) tuples that must NOT be paired again this weekend
                 (e.g. already scheduled) — a team never gets the same opponent.
    team_grounds: team_id -> set of ground_ids already used this weekend; the
                  scheduler avoids giving a team the same ground twice.
    """
    home_ground = home_ground or {}
    avoid_pairs = avoid_pairs or set()
    used_grounds = {t: set(g) for t, g in (team_grounds or {}).items()}

    def h2h(a: str, b: str) -> int:
        return head_to_head.get(tuple(sorted((a, b))), 0)

    # Rank all candidate pairs by fewest previous meetings (skip forbidden repeats).
    candidates = [p for p in combinations(team_ids, 2) if tuple(sorted(p)) not in avoid_pairs]
    candidates.sort(key=lambda p: (h2h(*p), p))

    used: set[str] = set()
    pairings: list[Pairing] = []
    round_grounds: set[str] = set()   # grounds already used in THIS schedule
    ground_cursor = 0
    for a, b in candidates:
        if a in used or b in used:
            continue
        # Give each fixture a DIFFERENT ground (can't play two matches on one
        # ground at once). Prefer one not used this round and not already used
        # by either team this weekend; degrade gracefully only if grounds run out.
        ground = None
        if grounds:
            taken = used_grounds.get(a, set()) | used_grounds.get(b, set())
            ground = (next((g for g in grounds if g not in round_grounds and g not in taken), None)
                      or next((g for g in grounds if g not in round_grounds), None)
                      or next((g for g in grounds if g not in taken), None)
                      or grounds[ground_cursor % len(grounds)])
            ground_cursor += 1
            round_grounds.add(ground)
            used_grounds.setdefault(a, set()).add(ground)
            used_grounds.setdefault(b, set()).add(ground)
        pairings.append(Pairing(a, b, ground, h2h(a, b)))
        used.update((a, b))

    byes = [t for t in team_ids if t not in used]

    # Fairness score: variance of resulting matchup counts (lower is better).
    counts = [p.meetings_so_far for p in pairings]
    mean = sum(counts) / len(counts) if counts else 0
    variance = sum((c - mean) ** 2 for c in counts) / len(counts) if counts else 0.0

    return ScheduleResult(pairings=pairings, byes=byes, fairness_score=round(variance, 3))
