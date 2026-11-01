import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

CORE = "https://core-prod-origin.cricclubs.com/core/public"
SERIES = "cvCS9qKLQS3LzGnLIu3HMA"
LEAGUE = "UoXwCQL2LQ6sNXXWuDSkjA"
OUT = Path(__file__).resolve().parent.parent / "data"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def shape(v, depth=0):
    pad = "  " * depth
    if isinstance(v, dict):
        return "{\n" + "\n".join(f"{pad}  {k}: {shape(val, depth+1)}" for k, val in list(v.items())[:40]) + f"\n{pad}}}"
    if isinstance(v, list):
        return f"[{len(v)}] " + (shape(v[0], depth) if v else "")
    return type(v).__name__


with sync_playwright() as p:
    req = p.request.new_context(extra_http_headers={"User-Agent": UA, "Accept": "application/json",
                                                    "Origin": "https://www.cricclubs.com",
                                                    "Referer": "https://www.cricclubs.com/"})
    # teams
    r = req.get(f"{CORE}/series/{SERIES}/teams?leagueId={LEAGUE}&year=2026")
    teams = r.json()
    (OUT / "teams.json").write_text(json.dumps(teams, indent=2), encoding="utf-8")
    print("TEAMS status", r.status)
    print("TEAMS shape:", shape(teams)[:1200])

    # matches (completed with scorecard)
    r2 = req.get(f"{CORE}/series/{SERIES}/matches?year=2026&status=hasMatch&teamId=&day=&leagueId={LEAGUE}&page=1&size=100")
    m = r2.json()
    (OUT / "matches_hasMatch.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
    print("\nMATCHES(hasMatch) status", r2.status)
    print("MATCHES shape:", shape(m)[:1800])
    req.dispose()
