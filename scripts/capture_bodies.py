import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.cricclubs.com/WagholiSocietyCricketCouncil"
Q = "?leagueId=UoXwCQL2LQ6sNXXWuDSkjA&year=2026&series=cvCS9qKLQS3LzGnLIu3HMA&seriesName=2026+-+WSCC+Cricket+Council"
OUT = Path(__file__).resolve().parent.parent / "data"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

bodies = {}

def on_response(resp):
    u = resp.url
    if "core-prod-origin.cricclubs.com" in u and ("/teams?" in u or "/matches?" in u):
        try:
            bodies[u] = resp.json()
        except Exception as e:
            bodies[u] = {"_error": str(e)}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(user_agent=UA, viewport={"width": 1366, "height": 900}).new_page()
    page.on("response", on_response)
    page.goto(BASE + "/teams" + Q, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    page.goto(BASE + "/results" + Q, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    b.close()

def summarize(label, data):
    print(f"\n### {label}")
    if isinstance(data, dict):
        print("  keys:", list(data.keys()))
        for k, v in data.items():
            if isinstance(v, list):
                print(f"  {k}: list[{len(v)}]")
                if v:
                    print("    sample item keys:", list(v[0].keys()) if isinstance(v[0], dict) else type(v[0]).__name__)
    elif isinstance(data, list):
        print(f"  list[{len(data)}] item keys:", list(data[0].keys()) if data and isinstance(data[0], dict) else "")

for u, data in bodies.items():
    tag = "TEAMS" if "/teams?" in u else "MATCHES"
    fn = "teams.json" if tag == "TEAMS" else "matches.json"
    (OUT / fn).write_text(json.dumps(data, indent=2), encoding="utf-8")
    summarize(tag + "  " + u.split("/public/")[-1][:60], data)

print("\nsaved:", [("teams.json" if "/teams?" in u else "matches.json") for u in bodies])
