#!/usr/bin/env bash
set -euo pipefail

# Headless login for gh (so copilot can use authenticated gh context)
if [ -n "${COPILOT_PAT:-}" ]; then
  echo "Logging in gh with provided PAT..."
  echo "${COPILOT_PAT}" | gh auth login --with-token
fi

# Optional: verify copilot binary present
if command -v copilot >/dev/null 2>&1; then
  echo "copilot binary found: $(command -v copilot)"
else
  echo "Warning: copilot binary not found in PATH"
fi

# Start production WSGI server
exec gunicorn -b 0.0.0.0:5000 app:app