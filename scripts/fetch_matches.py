import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

LEAGUE = "UoXwCQL2LQ6sNXXWuDSkjA"
MATCH_SERIES = "IJnTA0-FLADHspLBnvqFJg"   # the series that actually has matches
CORE = "https://core-prod-origin.cricclubs.com/core/public"
OUT = Path(__file__).resolve().parent.parent / "data"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

RESULTS_URL = (f"https://www.cricclubs.com/WagholiSocietyCricketCouncil/results"
               f"?leagueId={LEAGUE}&year=2026&series={MATCH_SERIES}&seriesName=WSCC")

first_body = {}
match_token = {}

def on_response(resp):
    if f"/series/{MATCH_SERIES}/matches?" in resp.url:
        try:
            first_body["data"] = resp.json()
            first_body["url"] = resp.url
        except Exception:
            pass

def on_request(req):
    if f"/series/{MATCH_SERIES}/matches?" in req.url:
        tok = req.headers.get("x-content-token")
        if tok:
            match_token["t"] = tok

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(user_agent=UA, viewport={"width": 1366, "height": 900})
    page = ctx.new_page()
    page.on("response", on_response)
    page.on("request", on_request)
    page.goto(RESULTS_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)
    print("first matches call URL:", first_body.get("url"))
    print("token captured:", bool(match_token.get("t")))

    all_matches = []
    d = first_body.get("data")
    if d:
        (OUT / "matches_page1.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
        payload = d.get("data", d)
        lst = payload.get("all") if isinstance(payload, dict) else payload
        print("page1 payload keys:", list(payload.keys()) if isinstance(payload, dict) else len(payload))
        if isinstance(lst, list):
            print("page1 match count:", len(lst))
            all_matches += lst

    # page through the rest using the captured token (same browser context request)
    tok = match_token.get("t")
    if tok:
        headers = {"x-content-token": tok, "accept": "application/json",
                   "referer": "https://www.cricclubs.com/", "user-agent": UA}
        for pg in range(2, 8):
            url = f"{CORE}/series/{MATCH_SERIES}/matches?year=2026&status=hasMatch&teamId=&day=&leagueId={LEAGUE}&page={pg}&size=30"
            r = ctx.request.get(url, headers=headers)
            if r.status != 200:
                print(f"page {pg}: HTTP {r.status} (stop)"); break
            pd = r.json().get("data", {})
            lst = pd.get("all") if isinstance(pd, dict) else pd
            if not lst:
                print(f"page {pg}: empty (stop)"); break
            all_matches += lst
            print(f"page {pg}: +{len(lst)}")

    (OUT / "all_matches.json").write_text(json.dumps(all_matches, indent=2), encoding="utf-8")
    print("\nTOTAL matches collected:", len(all_matches))
    b.close()
