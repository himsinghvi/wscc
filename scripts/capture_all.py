import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://www.cricclubs.com/WagholiSocietyCricketCouncil"
Q = "?leagueId=UoXwCQL2LQ6sNXXWuDSkjA&year=2026&series=cvCS9qKLQS3LzGnLIu3HMA&seriesName=2026+-+WSCC+Cricket+Council"
OUT = Path(__file__).resolve().parent.parent / "data" / "api"
OUT.mkdir(parents=True, exist_ok=True)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

items = []
def on_response(resp):
    u = resp.url
    if "core-prod-origin.cricclubs.com/core/public" in u:
        try:
            data = resp.json()
        except Exception:
            return
        items.append((u, data))

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(user_agent=UA, viewport={"width": 1366, "height": 900}).new_page()
    page.on("response", on_response)
    for path in ["/teams", "/results", ""]:
        page.goto(BASE + path + Q, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
    b.close()

print(f"captured {len(items)} core responses\n")
idx = 0
for u, data in items:
    short = u.split("/core/public/")[-1]
    name = re.sub(r"[^a-zA-Z0-9]+", "_", short)[:70]
    (OUT / f"{idx:02d}_{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    # summarise
    d = data.get("data") if isinstance(data, dict) else data
    n = len(d) if isinstance(d, (list, dict)) else "-"
    print(f"[{idx:02d}] {short[:85]}  (data len={n})")
    idx += 1
