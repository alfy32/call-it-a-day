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

## Database Backups

`scripts/backup.sh` creates a timestamped copy of the database and removes copies older than 21 days.

It uses `sqlite3 .backup` which is safe to run while the server is running — no need to stop the container.

**One-time setup:**

```bash
# Install sqlite3 if needed
sudo apt install sqlite3

# Test it manually first
sudo bash /path/to/call-it-a-day/scripts/backup.sh
```

**Schedule it with cron** (runs daily at 2 AM):

```bash
sudo crontab -e
```

Add this line:

```
0 2 * * * /path/to/call-it-a-day/scripts/backup.sh >> /var/log/callitaday-backup.log 2>&1
```

Backups land in `/var/lib/callitaday/backups/` as `callitaday-YYYY-MM-DD.db`. Each run cleans up anything older than 21 days.

To restore a backup, stop the container, copy the backup file over the database, then start again:

```bash
docker compose down
sudo cp /var/lib/callitaday/backups/callitaday-YYYY-MM-DD.db /var/lib/callitaday/callitaday.db
docker compose up -d
```

---

## Configuration

Settings (daily target, weekly target, tracking start date) are available via the web UI or the API:

```
GET  /api/settings
PATCH /api/settings
```
