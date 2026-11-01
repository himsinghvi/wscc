import json, sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

LEAGUE = "UoXwCQL2LQ6sNXXWuDSkjA"
BASE = "https://www.cricclubs.com/WagholiSocietyCricketCouncil"
Q = f"?leagueId={LEAGUE}&year=2026&series=IJnTA0-FLADHspLBnvqFJg&seriesName=WSCC"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

ground_json = []
def on_resp(r):
    u = r.url.lower()
    if "core-prod-origin" in u and any(k in u for k in ("ground", "venue", "field")):
        try:
            ground_json.append((r.url, r.json()))
        except Exception:
            pass

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(user_agent=UA).new_page()
    page.on("response", on_resp)
    # pages that might load grounds
    for path in ["/schedule", "/results", "/grounds", "/venues", "/statistics"]:
        try:
            page.goto(BASE + path + Q, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(3500)
        except Exception as e:
            print("skip", path, str(e)[:50])
    print("ground-ish responses:", len(ground_json))
    from pathlib import Path
    OUT = Path(__file__).resolve().parent.parent / "data"
    for u, d in ground_json:
        grounds = (d.get("data") or {}).get("grounds") or []
        if grounds:
            (OUT / "grounds.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
            print(f"\nSAVED {len(grounds)} grounds from {u[:80]}")
            for g in grounds:
                print(f"  {g['name']!r:22} id={g['id']}  addr={g.get('address','')!r}")
    b.close()
