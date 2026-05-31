#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$HOME/.config/callitaday"
CONFIG_FILE="$CONFIG_DIR/config"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE="callitaday-listener.service"
UNIT_FILE="$SYSTEMD_DIR/$SERVICE"

echo ""
echo "Call It a Day — Ubuntu Agent Uninstaller"
echo "─────────────────────────────────────────"
echo ""

# ── Stop and disable the service ─────────────────────────────────────────────
if systemctl --user is-active --quiet "$SERVICE" 2>/dev/null; then
  systemctl --user stop "$SERVICE"
  echo "Stopped $SERVICE."
fi

if systemctl --user is-enabled --quiet "$SERVICE" 2>/dev/null; then
  systemctl --user disable "$SERVICE"
  echo "Disabled $SERVICE."
fi

# ── Remove unit file ─────────────────────────────────────────────────────────
if [[ -f "$UNIT_FILE" ]]; then
  rm -f "$UNIT_FILE"
  echo "Removed $UNIT_FILE."
fi

systemctl --user daemon-reload

# ── Remove config ─────────────────────────────────────────────────────────────
if [[ -f "$CONFIG_FILE" ]]; then
  rm -f "$CONFIG_FILE"
  echo "Removed $CONFIG_FILE."
fi

if [[ -d "$CONFIG_DIR" ]] && [[ -z "$(ls -A "$CONFIG_DIR")" ]]; then
  rmdir "$CONFIG_DIR"
  echo "Removed $CONFIG_DIR."
fi

echo ""
echo "Done. The agent has been removed from this machine."
