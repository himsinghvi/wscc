"""Exploratory crawl of the CricClubs WSCC league to learn the page structure.
Saves rendered HTML and prints candidate links. Read-only."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

TEAMS_URL = ("https://www.cricclubs.com/WagholiSocietyCricketCouncil/teams"
             "?leagueId=UoXwCQL2LQ6sNXXWuDSkjA&year=2026"
             "&series=cvCS9qKLQS3LzGnLIu3HMA&seriesName=2026+-+WSCC+Cricket+Council")

OUT = Path(__file__).resolve().parent.parent / "data"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        page.goto(TEAMS_URL, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(3000)

        html = page.content()
        (OUT / "teams.html").write_text(html, encoding="utf-8")
        page.screenshot(path=str(OUT / "teams.png"), full_page=True)
        print("TITLE:", page.title())
        print("URL:", page.url)
        print("HTML bytes:", len(html))
        body_text = page.inner_text("body")[:600]
        print("\n--- BODY TEXT (first 600) ---\n", body_text)

        # candidate team links
        links = page.eval_on_selector_all(
            "a",
            """els => els.map(e => ({text: (e.innerText||'').trim(), href: e.getAttribute('href')||''}))
                        .filter(x => x.href.includes('teamView') || x.href.includes('team') )
                        .slice(0, 60)""",
        )
        print("\n--- TEAM-ish LINKS ---")
        for l in links:
            if l["text"]:
                print(f"  {l['text'][:40]:40} -> {l['href']}")

        # nav links (to find schedule / matches pages)
        nav = page.eval_on_selector_all(
            "a",
            """els => els.map(e => ({text:(e.innerText||'').trim(), href:e.getAttribute('href')||''}))
                        .filter(x => /schedul|match|fixture|result|standing|score/i.test(x.href+x.text))
                        .slice(0,40)""",
        )
        print("\n--- SCHEDULE/MATCH NAV ---")
        seen = set()
        for l in nav:
            key = l["href"]
            if key in seen:
                continue
            seen.add(key)
            print(f"  {l['text'][:30]:30} -> {l['href']}")

        browser.close()


if __name__ == "__main__":
    main()
