"""Azure OpenAI integration (feature 8 — AI assist).

Used to generate a human-readable explanation of the deterministic schedule and
to answer "why was this fixture chosen" style questions. Degrades gracefully to
a templated explanation when Azure OpenAI is not configured.
"""
from __future__ import annotations

from ..core.config import settings
from .scheduler import ScheduleResult

try:
    from openai import AzureOpenAI
except Exception:
    AzureOpenAI = None  # type: ignore


def _client():
    if not (AzureOpenAI and settings.azure_openai_endpoint and settings.azure_openai_api_key):
        return None
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


def _template_explanation(result: ScheduleResult, team_names: dict[str, str]) -> str:
    lines = ["Here is this weekend's fixture, optimised for fair matchups:"]
    for p in result.pairings:
        lines.append(
            f"• {team_names.get(p.home_team_id, p.home_team_id)} vs "
            f"{team_names.get(p.away_team_id, p.away_team_id)} "
            f"(met {p.meetings_so_far}× before)"
        )
    if result.byes:
        lines.append("Byes: " + ", ".join(team_names.get(b, b) for b in result.byes))
    lines.append(f"Fairness score (lower is fairer): {result.fairness_score}")
    return "\n".join(lines)


def explain_schedule(result: ScheduleResult, team_names: dict[str, str]) -> dict:
    """Return {explanation, source} — AI when available, else template."""
    template = _template_explanation(result, team_names)
    client = _client()
    if client is None:
        return {"explanation": template, "source": "template"}

    prompt = (
        "You are a cricket league scheduler assistant. Explain to captains, in a "
        "friendly concise way, why these fixtures are fair. Emphasise that pairs who "
        "have met the fewest times were prioritised and grounds were rotated.\n\n"
        f"Fixtures:\n{template}"
    )
    try:
        resp = client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=400,
        )
        return {"explanation": resp.choices[0].message.content, "source": "azure_openai"}
    except Exception as e:  # never fail the request because of AI
        return {"explanation": template, "source": f"template_fallback ({e})"}
