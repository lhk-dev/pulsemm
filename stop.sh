#!/usr/bin/env bash
echo "Stopping Pulse Myanmar..."
lsof -ti :8765 | xargs kill -9 2>/dev/null || true
echo "Pulse Myanmar stopped."
