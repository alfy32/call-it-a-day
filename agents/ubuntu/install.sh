#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(realpath "$0")")" && pwd)"
LISTENER_PY="$SCRIPT_DIR/listener.py"
CONFIG_DIR="$HOME/.config/callitaday"
CONFIG_FILE="$CONFIG_DIR/config"
SYSTEMD_DIR="$HOME/.config/systemd/user"

# ── Load existing values for re-run UX ──────────────────────────────────────
current_url=""
current_name=""
if [[ -f "$CONFIG_FILE" ]]; then
  current_url=$(grep '^CALLITADAY_SERVER_URL=' "$CONFIG_FILE" | cut -d= -f2- || true)
  current_name=$(grep '^CALLITADAY_COMPUTER_NAME=' "$CONFIG_FILE" | cut -d= -f2- || true)
fi
default_name="${current_name:-$(hostname)}"

echo ""
echo "Call It a Day — Ubuntu Agent Installer"
echo "──────────────────────────────────────"
echo ""

if [[ -n "$current_url" ]]; then
  read -rp "Server URL [$current_url]: " input_url
  SERVER_URL="${input_url:-$current_url}"
else
  read -rp "Server URL (e.g. http://192.168.1.10:8001): " SERVER_URL
fi

read -rp "Computer name [$default_name]: " input_name
COMPUTER_NAME="${input_name:-$default_name}"

if [[ -z "$SERVER_URL" ]]; then
  echo "Error: Server URL cannot be empty." >&2
  exit 1
fi
if [[ "$COMPUTER_NAME" == *" "* ]]; then
  echo "Error: Computer name cannot contain spaces." >&2
  exit 1
fi

# ── Check python3-dbus ───────────────────────────────────────────────────────
if ! python3 -c "import dbus" 2>/dev/null; then
  echo "Installing python3-dbus…"
  sudo apt-get install -y python3-dbus python3-gi
fi

# ── Write config ─────────────────────────────────────────────────────────────
mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_FILE" <<EOF
CALLITADAY_SERVER_URL=$SERVER_URL
CALLITADAY_COMPUTER_NAME=$COMPUTER_NAME
EOF
chmod 600 "$CONFIG_FILE"
echo "Wrote $CONFIG_FILE"

# ── Write systemd unit ───────────────────────────────────────────────────────
mkdir -p "$SYSTEMD_DIR"

cat > "$SYSTEMD_DIR/callitaday-listener.service" <<EOF
[Unit]
Description=Call It a Day — screen lock/unlock listener
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
EnvironmentFile=-%h/.config/callitaday/config
ExecStart=/usr/bin/python3 "$LISTENER_PY"
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
EOF

echo "Wrote systemd unit to $SYSTEMD_DIR/callitaday-listener.service"

# ── Enable and start ─────────────────────────────────────────────────────────
systemctl --user daemon-reload
systemctl --user enable callitaday-listener.service
systemctl --user restart callitaday-listener.service
echo "Listener enabled and started."

echo ""
echo "Done. Logs: journalctl --user -u callitaday-listener -f"
