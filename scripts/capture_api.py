import sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.cricclubs.com/WagholiSocietyCricketCouncil"
Q = "?leagueId=UoXwCQL2LQ6sNXXWuDSkjA&year=2026&series=cvCS9qKLQS3LzGnLIu3HMA&seriesName=2026+-+WSCC+Cricket+Council"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

hits = []

def on_response(resp):
    try:
        ct = resp.headers.get("content-type", "")
        url = resp.url
        if "application/json" in ct and "cricclubs.com" in url and "_next" not in url:
            hits.append((resp.request.method, resp.status, url))
    except Exception:
        pass

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(user_agent=UA, viewport={"width": 1366, "height": 900}).new_page()
    page.on("response", on_response)
    for path in ["/teams", "/results"]:
        print(f"\n### loading {path}")
        page.goto(BASE + path + Q, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
    print("\n--- JSON API CALLS ---")
    for m, s, u in hits:
        print(f"  {m} {s}  {u}")
    b.close()
