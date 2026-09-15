#!/bin/sh
set -eu

# Bind mounts on Docker Desktop (macOS) break Turbopack's package resolution.
export WATCHPACK_POLLING=true
export CHOKIDAR_USEPOLLING=true
export CHOKIDAR_INTERVAL=1000

API_URL="${INTERNAL_API_URL:-http://backend:8000}"
i=0
while [ "$i" -lt 40 ]; do
  if wget -qO- "$API_URL/health" >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 1
done

cd /workspace/uis/website
./node_modules/.bin/next dev --webpack --port 3000 --hostname 0.0.0.0 &

cd /workspace/uis/backoffice
./node_modules/.bin/next dev --webpack --port 3001 --hostname 0.0.0.0 &

wait
