#!/usr/bin/env bash
# Daily database backup for Call It a Day.
# Creates a timestamped copy and removes backups older than 21 days.
#
# Usage: run via cron, or manually:
#   sudo bash /path/to/backup.sh
#
# Configure via env vars or edit the defaults below.

set -euo pipefail

DB="${CALLITADAY_DB:-/var/lib/callitaday/callitaday.db}"
BACKUP_DIR="${CALLITADAY_BACKUP_DIR:-/var/lib/callitaday/backups}"
KEEP_DAYS="${CALLITADAY_KEEP_DAYS:-21}"

mkdir -p "$BACKUP_DIR"

DEST="$BACKUP_DIR/callitaday-$(date +%Y-%m-%d).db"

# sqlite3 .backup handles WAL mode safely — no need to stop the server
sqlite3 "$DB" ".backup '$DEST'"

echo "Backed up to $DEST"

# Remove backups older than KEEP_DAYS
find "$BACKUP_DIR" -name 'callitaday-*.db' -mtime +"$KEEP_DAYS" -delete -print \
  | sed 's/^/Removed: /'
