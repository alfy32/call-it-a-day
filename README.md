# Call It a Day

A self-hosted work-time tracker that answers one question: **have you worked enough today?**

Log in to your computer and it tracks itself. No timers, no manual start/stop. At the end of the day, you'll know.

---

## How It Works

Lightweight agents run on each of your computers and watch for screen lock/unlock events. When you unlock, a session starts. When you lock (or shut down), it ends. The server stores those sessions and serves a web UI that tells you where you stand.

The dashboard shows your hours for the day, a progress bar toward your daily goal, and when you can stop. Once you've hit your hours it says: *You've earned it. Call it a day.*

---

## Running the Server

Requires Docker.

```bash
docker compose up -d
```

The server runs on port **8001** and stores its database at `/var/lib/callitaday/callitaday.db` on the host.

To change the port, edit `docker-compose.yml`. To move the database, update the `volumes` line.

---

## Setting Up an Agent

### Ubuntu (GNOME)

```bash
bash agents/ubuntu/install.sh
```

The installer will ask for your server URL and a name for this computer, then set up a systemd user service that starts automatically with your graphical session.

Logs: `journalctl --user -u callitaday-listener -f`

---

## Configuration

Settings (daily target, weekly target, tracking start date) are available via the web UI or the API:

```
GET  /api/settings
PATCH /api/settings
```

---

## Docs

- [DESIGN.md](docs/DESIGN.md) — architecture, data model, and design decisions
- [BRANDING.md](docs/BRANDING.md) — visual identity, colors, and typography
