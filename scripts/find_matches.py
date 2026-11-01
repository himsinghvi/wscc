"""Click the Matches nav to discover the matches URL + structure."""
from pathlib import Path
from playwright.sync_api import sync_playwright

TEAMS_URL = ("https://www.cricclubs.com/WagholiSocietyCricketCouncil/teams"
             "?leagueId=UoXwCQL2LQ6sNXXWuDSkjA&year=2026"
             "&series=cvCS9qKLQS3LzGnLIu3HMA&seriesName=2026+-+WSCC+Cricket+Council")
OUT = Path(__file__).resolve().parent.parent / "data"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(user_agent=UA, viewport={"width": 1366, "height": 900}).new_page()
    page.goto(TEAMS_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)

    # click the top-nav "Matches" link
    try:
        page.get_by_role("link", name="Matches", exact=True).first.click(timeout=8000)
    except Exception as e:
        print("click failed:", e)
        # try a menu item
        page.get_by_text("Matches", exact=True).first.click(timeout=8000)
    page.wait_for_timeout(4000)

    print("MATCHES URL:", page.url)
    (OUT / "matches.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(OUT / "matches.png"), full_page=True)
    print("\n--- BODY TEXT (first 2000) ---\n", page.inner_text("body")[:2000])
    b.close()
