#!/usr/bin/env bash
set -euo pipefail


# Start production WSGI server
exec gunicorn -b 0.0.0.0:5000 app:app