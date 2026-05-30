# Call It a Day

A self-hosted work-time tracker that answers one question: **have you worked enough today?**

Log in to your computer and it tracks itself. No timers, no manual start/stop. At the end of the day, you'll know.

---

## What's Different from v1

v1 ([worktime-tracker](https://github.com/alfy32/worktime-tracker)) logged raw login/logout events and reconstructed session state at display time. v2 stores three distinct record types instead:

| Type | Description |
|------|-------------|
| **Active Sessions** | A start with no end — one expected per computer. Extras indicate a missed logout. |
| **Complete Sessions** | A start and an end. Primary source of truth for work history. |
| **Manual Entries** | Manually added time blocks for WFH days, travel, exceptions. |

The display layer shows complete sessions as the base, with active sessions layered on top. Active sessions get a distinct callout UI so you can see the live session and dismiss any orphaned ones.

---

## Architecture

**Stack:** Python / FastAPI, SQLite, SQLAlchemy — same core as v1.

**Agents:** Lightweight background processes running on each computer. They detect login/logout and screen lock/unlock events, then POST to the server.

**Server:** Exposes a REST API and serves the web UI. Runs in Docker.

**Storage:** A single SQLite database file, kept outside the container so it survives redeploys.

**Future:** The app may grow beyond a simple local deployment — a hosted multi-user version is a possibility. The architecture is designed to not preclude that.

---

## Design

**Name:** Call It a Day

**Tagline:** *Have you worked enough today?*

**Tone:** Quiet, earned, honest. The app doesn't cheer — it confirms. Hitting your hours should feel like a nod, not a party.

**Colors:**
- Background: `#F8FAFC` (cool white)
- Primary accent: `#4F46E5` (indigo)
- Done state: `#059669` (emerald)
- Text: `#0F172A` / `#64748B` (slate 900 / 500)

**Typography:**
- UI labels / headings: Plus Jakarta Sans
- Body / secondary: Inter
- Time values: JetBrains Mono

**Icon:** Indigo circle with a clock face showing a progress arc that fills as the day completes.

---

## Status

Early design phase. Branding and architecture are decided; implementation not yet started.

→ See [BRANDING.md](docs/BRANDING.md) for the full visual guide
→ See [DESIGN.md](docs/DESIGN.md) for architecture and design decisions
