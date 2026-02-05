#!/usr/bin/env bash
set -euo pipefail

# install.sh
# Install helper for developer machine (Linux Debian/Ubuntu).
# - installs system prerequisites (curl, ca-certificates, build-essential)
# - installs Python dependencies from requirements.txt

# Usage: chmod +x install.sh && ./install.sh

function info { echo -e "\e[34m[INFO]\e[0m $*"; }
function warn { echo -e "\e[33m[WARN]\e[0m $*"; }
function err { echo -e "\e[31m[ERROR]\e[0m $*"; }

# Detect OS family
OS="unknown"
if [ -f /etc/debian_version ]; then
  OS="debian"
elif [ "$(uname)" = "Darwin" ]; then
  OS="macos"
fi

info "Detected OS: $OS"

if [ "$OS" = "debian" ]; then
  info "Installing apt prerequisites (may require sudo)"
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends curl ca-certificates build-essential python3 python3-pip python3-venv
fi

# Check Python version
if command -v python3 >/dev/null 2>&1; then
  info "Python version: $(python3 --version)"
else
  err "Python3 not found. Please install Python 3.9+ first."
  exit 1
fi

# Create virtual environment if not exists
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  info "Creating virtual environment in $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# Activate venv and install dependencies
info "Activating virtual environment and installing dependencies..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r requirements.txt

info "Installation complete."

cat <<'EOF'
Next steps:
- Activate the virtual environment: source .venv/bin/activate
- Run the Flask app: python app.py
- Or run with gunicorn: gunicorn -b 0.0.0.0:5000 app:app

For production deployment:
- Build Docker image: docker build -t doyoureallyneedai .
- Run container: docker run -p 5000:5000 doyoureallyneedai
EOF

exit 0

