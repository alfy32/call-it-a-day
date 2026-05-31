# Call It a Day

A self-hosted work-time tracker that answers one question: **have you worked enough today?**

Log in to your computer and it tracks itself. No timers, no manual start/stop. At the end of the day, you'll know.

---

## How It Works

Lightweight agents run on each of your computers and watch for screen lock/unlock events. When you unlock, a session starts. When you lock (or shut down), it ends. The server stores those sessions and serves a web UI that tells you where you stand.

The dashboard shows your hours for the day, a progress bar toward your daily goal, and when you can stop. Once you've hit your hours it says: *You've earned it. Call it a day.*

---

## Docs

- [SETUP.md](SETUP.md) — running the server, installing agents, configuration
- [DESIGN.md](docs/DESIGN.md) — architecture, data model, and design decisions
- [BRANDING.md](docs/BRANDING.md) — visual identity, colors, and typography
