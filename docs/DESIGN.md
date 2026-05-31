# Call It a Day — Design Doc

## Overview

**Call It a Day** (callitaday.work) — v2 of worktime-tracker.

Core question the app answers: *"Have I worked enough today — can I call it a day?"*

Based on: https://github.com/alfy32/worktime-tracker (also at ~/projects/personal/worktime-tracker)

---

## Problem with v1

v1 logged raw login/logout events and reconstructed session state at display time. This made the data model fragile — if an event was missed or malformed, the reconstructed sessions would be wrong with no easy way to detect or correct it.

---

## Data Storage Architecture

v2 uses three distinct record types instead of an event log:

### 1. Active Sessions
- Have a **start** but **no end**
- Represent currently running work sessions
- **Expected:** one active session per computer

**Invalid data flags — both conditions flag the session in the UI for review:**
- **Duration > 12 hours** — probably a missed logout or crash; stop counting time beyond the 12h mark when calculating today's total. The raw record is kept as-is; only display math is capped.
- **More than one active session per computer** — same class of problem (missed logout/crash).

Flagged sessions are surfaced in the UI so the user can dismiss or correct them. They are never silently auto-closed — the stored data stays honest.

### 2. Complete Sessions
- Have both a **start** and an **end**
- Primary source of truth for displaying work history
- Sessions that cross midnight are attributed to the start day — no splitting

### 3. Manual Entries
- Manually added time blocks — flexible, three valid forms:
  - **Full range** — start + end (e.g. 7:00 AM – 8:00 AM)
  - **Start only** — start + duration, no end time
  - **Hours only** — a duration with no specific time anchor (e.g. "2h for on-call coverage")
- All three count toward the daily total

### Display Logic
- Render complete sessions as the base
- Layer active sessions on top with a distinct callout UI
- Callout lets users see the live session and dismiss orphaned ones

---

## Tech Stack

**Server:** Python / FastAPI + SQLite + SQLAlchemy — same core as v1. Familiar, lightweight, no infra overhead for a self-hosted app.

**Agents:** Lightweight background processes on each computer. Detect login/logout and screen lock/unlock, POST to the server. Same model as v1.

**Deployment:** Docker + Docker Compose. Database file kept outside the container.

**Future scope:** The app may grow beyond local self-hosting — a multi-user hosted version is a possibility. Stack choices don't preclude that, but it's not the current target.

---

## Branding

- **Name:** Call It a Day
- **Domain:** callitaday.work
- **Tone:** Quiet, earned, honest. Confirms rather than celebrates. Hitting your hours should feel like a nod, not a party.
- **Colors:** Indigo primary (`#4F46E5`), emerald done state (`#059669`), slate neutrals
- **Typography:** Plus Jakarta Sans (UI), Inter (body), JetBrains Mono (time values)
- **Icon:** Clock face on indigo background — progress arc fills as the day completes

Full visual guide: [BRANDING.md](BRANDING.md)

---

## v2 Ideas (Backlog)

- Weekly carry-forward (surplus/deficit from prior weeks affects daily target) — this existed in v1
- Per-computer session log with is-work toggles — existed in v1
- Daily and weekly charts — existed in v1
- Multi-user / hosted version as a future possibility

---

## Status

Server, dashboard, weekly view, and Ubuntu agent implemented. Mockups at `docs/mockups/`.
