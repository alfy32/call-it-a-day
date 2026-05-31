#!/usr/bin/env bash
# Pull the latest code and restart the server.
set -euo pipefail

cd "$(dirname "$(realpath "$0")")/.."

git pull
docker compose up -d --build
