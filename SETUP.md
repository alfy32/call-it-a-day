# Setup

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
