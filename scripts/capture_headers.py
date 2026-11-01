import sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.cricclubs.com/WagholiSocietyCricketCouncil"
Q = "?leagueId=UoXwCQL2LQ6sNXXWuDSkjA&year=2026&series=cvCS9qKLQS3LzGnLIu3HMA&seriesName=2026+-+WSCC+Cricket+Council"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

captured = {}

def on_request(req):
    if "core-prod-origin.cricclubs.com" in req.url and ("/teams" in req.url or "/matches" in req.url):
        captured[req.url] = req.headers

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(user_agent=UA).new_page()
    page.on("request", on_request)
    page.goto(BASE + "/teams" + Q, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    page.goto(BASE + "/results" + Q, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    for url, hdrs in captured.items():
        print("\nURL:", url)
        for k, v in hdrs.items():
            print(f"   {k}: {v[:80]}")
    b.close()
