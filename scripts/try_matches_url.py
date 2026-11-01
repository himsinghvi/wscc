from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "https://www.cricclubs.com/WagholiSocietyCricketCouncil"
Q = "?leagueId=UoXwCQL2LQ6sNXXWuDSkjA&year=2026&series=cvCS9qKLQS3LzGnLIu3HMA&seriesName=2026+-+WSCC+Cricket+Council"
OUT = Path(__file__).resolve().parent.parent / "data"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

CANDIDATES = ["/matches", "/viewAllMatches", "/schedule", "/results"]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(user_agent=UA, viewport={"width": 1366, "height": 900}).new_page()
    for path in CANDIDATES:
        url = BASE + path + Q
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3500)
            title = page.title()
            body = page.inner_text("body")[:400].replace("\n", " ")
            is404 = "not found" in title.lower() or "404" in title
            print(f"\n=== {path} -> {page.url}")
            print(f"    title: {title}")
            print(f"    body: {body[:300]}")
            if "match" in title.lower() or "schedul" in title.lower():
                (OUT / "matches.html").write_text(page.content(), encoding="utf-8")
                print("    *** saved matches.html ***")
        except Exception as e:
            print(f"\n=== {path} -> ERROR {str(e)[:80]}")
    b.close()
