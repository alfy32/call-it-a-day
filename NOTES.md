# Call It a Day — Brainstorming Notes

> Status: In progress — capturing context before session restart

## What We're Building

**Call It a Day** (callitaday.com) — v2 of worktime-tracker.

Core question the app answers: *"Have I worked enough today — can I call it a day?"*

Based on: https://github.com/alfy32/worktime-tracker (also at ~/projects/personal/worktime-tracker)

---

## Key Design Decision: Data Storage Architecture

The biggest change from v1 is how sessions are stored. Instead of logging every login/logout event and reconstructing state at display time, v2 uses three distinct record types:

### 1. Active Sessions
- Have a **start** but **no end**
- Represent currently running work sessions
- **Expected:** one active session per computer
- Extra active sessions = bug (session started but never ended)
- Users can flag extras as errors or view them as live sessions

### 2. Complete Sessions
- Have both a **start** and an **end**
- Primary source of truth for displaying work history

### 3. Manual Entries
- Manually added time blocks (same as v1)

### Display Logic
- Show data based on complete sessions
- Add active sessions on top of that
- Highlight/call out active sessions so users can:
  - See the current live session
  - Identify and dismiss erroneous open sessions

---

## Branding

- New name: **Call It a Day**
- Goal: proper rebrand — v1 was "worktime-tracker," built quickly to get tracking started
- Branding work was started but not completed in this session (visual companion had server issues)
- Still to explore: color palette, tone, logo direction, UI feel

---

## Next Steps (where we left off)

1. Finish branding exploration (visual companion or terminal-based)
2. Draft the README as the primary design doc entry point
3. Document tech stack decisions (not yet discussed)
4. Capture any remaining new ideas for v2
