import sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

TEAMS_URL = ("https://www.cricclubs.com/WagholiSocietyCricketCouncil/teams"
             "?leagueId=UoXwCQL2LQ6sNXXWuDSkjA&year=2026"
             "&series=cvCS9qKLQS3LzGnLIu3HMA&seriesName=2026+-+WSCC+Cricket+Council")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(user_agent=UA, viewport={"width": 1366, "height": 900}).new_page()
    page.goto(TEAMS_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3500)
    anchors = page.eval_on_selector_all(
        "a", "els => els.map(e => ({t:(e.innerText||'').trim(), h:e.getAttribute('href')||''}))")
    want = {"matches", "statistics", "members", "home", "series", "league", "standings", "points"}
    print("--- NAV ROUTES ---")
    seen = set()
    for a in anchors:
        t = a["t"].lower()
        if t in want and a["h"] not in seen:
            seen.add(a["h"]); print(f"  {a['t']:14} -> {a['h']}")
    # also dump any href containing these keywords
    print("--- href keyword scan ---")
    for a in anchors:
        h = a["h"].lower()
        if any(k in h for k in ("match", "schedul", "fixture", "score", "standing", "points", "result")):
            if a["h"] not in seen:
                seen.add(a["h"]); print(f"  {a['t'][:14]:14} -> {a['h']}")
    b.close()
