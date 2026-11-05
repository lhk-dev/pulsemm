#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Check if already running on port 8765
if lsof -ti :8765 >/dev/null 2>&1; then
    echo "Pulse Myanmar is already running on port 8765."
else
    echo "Starting Pulse Myanmar on http://0.0.0.0:8765..."
    nohup "$DIR/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8765 > "$DIR/pulsemm.log" 2>&1 &
    sleep 1.5
fi

echo "Opening Pulse Myanmar in browser..."
open "http://localhost:8765"
echo "Done! You can also access it on your tablet at: http://Ling.local:8765"
