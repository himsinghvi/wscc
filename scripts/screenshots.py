"""Capture screenshots of the running app (http://localhost:8077) for the README.
Seeds demo data via /api/dev/simulate, then shoots each page as the right persona."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://localhost:8077"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
VP = {"width": 1366, "height": 900}


def set_persona(page, email):
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.evaluate("(e) => { localStorage.setItem('wscc_dev_email', e); localStorage.setItem('wscc_jti', crypto.randomUUID()); }", email)


def shot(page, route, name, wait=1400, before=None):
    page.goto(BASE + route, wait_until="domcontentloaded")
    page.wait_for_timeout(wait)
    if before:
        try:
            before(page)
        except Exception as e:
            print("  before() failed:", e)
        page.wait_for_timeout(1200)
    page.screenshot(path=str(OUT / name))
    print("  saved", name)


with sync_playwright() as p:
    # 1) seed demo data as admin
    req = p.request.new_context(extra_http_headers={"X-Dev-Email": "admin@wscc.app"})
    req.post(f"{BASE}/api/dev/simulate", data={"num_teams": 12, "generate_schedule": True})
    teams = req.get(f"{BASE}/api/teams").json()["teams"]
    first_team = teams[0]["id"]
    req.dispose()

    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport=VP)
    page = ctx.new_page()

    # Login page: block /meta/me so the app shows the sign-in screen
    page.route("**/api/meta/me", lambda r: r.abort())
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT / "01-login.png")); print("  saved 01-login.png")
    page.unroute("**/api/meta/me")

    # Admin persona
    set_persona(page, "admin@wscc.app")
    shot(page, "/", "02-dashboard.png")
    shot(page, "/rankings", "04-rankings.png")
    shot(page, "/matches", "06-schedule-matches.png")
    shot(page, "/teams", "07-teams.png")
    shot(page, f"/teams/{first_team}", "08-team-detail.png")
    shot(page, "/grounds", "09-grounds.png")
    shot(page, "/stats", "10-stats.png")
    shot(page, "/tournaments", "11-tournaments.png")
    shot(page, "/scheduler", "12-scheduler.png", wait=1600,
         before=lambda pg: pg.get_by_role("button", name="Generate").first.click())
    shot(page, "/directory", "13-directory.png")
    shot(page, "/poll-schedule", "14-poll-schedule.png")
    shot(page, "/day-rules", "15-availability-rules.png")
    shot(page, "/admin", "16-admin.png")

    # Team persona (availability + backout)
    set_persona(page, "team1@wscc.test")
    shot(page, "/availability", "03-availability.png")
    shot(page, "/backout", "05-backout.png")

    b.close()
print("done ->", OUT)
