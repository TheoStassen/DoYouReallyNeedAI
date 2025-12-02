#!/usr/bin/env bash
set -euo pipefail

# install.sh
# Install helper for developer machine (Linux Debian/Ubuntu).
# - installs prerequisites (curl, ca-certificates, build-essential)
# - installs nvm and Node.js 22 via nvm
# - installs GitHub CLI (gh)
# - installs GitHub Copilot CLI via npm (global)

# Usage: chmod +x install.sh && ./install.sh

RECOMMENDED_NODE_VERSION=22
NVM_DIR="$HOME/.nvm"

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
  sudo apt-get install -y --no-install-recommends curl ca-certificates gnupg lsb-release build-essential
fi

# Install nvm if not present
if [ -s "$NVM_DIR/nvm.sh" ]; then
  info "nvm already installed"
  # shellcheck source=/dev/null
  source "$NVM_DIR/nvm.sh"
else
  info "Installing nvm (node version manager)"
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.6/install.sh | bash
  # Load nvm in current shell
  export NVM_DIR="$HOME/.nvm"
  # shellcheck source=/dev/null
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

# Ensure nvm is loaded
if ! command -v nvm >/dev/null 2>&1; then
  # try source
  if [ -s "$NVM_DIR/nvm.sh" ]; then
    # shellcheck source=/dev/null
    . "$NVM_DIR/nvm.sh"
  fi
fi

if ! command -v nvm >/dev/null 2>&1; then
  err "nvm installation failed or nvm is not available in this shell. Please start a new shell or source ~/.nvm/nvm.sh and re-run this script."
  exit 1
fi

info "Installing Node.js $RECOMMENDED_NODE_VERSION via nvm (this may take a minute)"
nvm install "$RECOMMENDED_NODE_VERSION"
nvm alias default "$RECOMMENDED_NODE_VERSION"
nvm use default

info "Node and npm versions after install:"
node -v || true
npm -v || true

# Install GitHub CLI (gh)
if command -v gh >/dev/null 2>&1; then
  info "GitHub CLI (gh) already installed: $(gh --version | head -n1)"
else
  if [ "$OS" = "debian" ]; then
    info "Installing GitHub CLI (gh) via apt (requires sudo)"
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg |
      sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg >/dev/null 2>&1 || true
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
    sudo apt-get update
    sudo apt-get install -y gh
    info "Installed gh: $(gh --version | head -n1)"
  elif [ "$OS" = "macos" ]; then
    if command -v brew >/dev/null 2>&1; then
      info "Installing gh via brew"
      brew install gh
    else
      warn "Homebrew not found — please install gh manually: https://github.com/cli/cli#installation"
    fi
  else
    warn "Unsupported OS for automated gh install — please install GitHub CLI manually: https://github.com/cli/cli#installation"
  fi
fi

# Install GitHub Copilot CLI via npm (global)
if command -v copilot >/dev/null 2>&1; then
  info "Copilot CLI already installed: $(copilot --version 2>/dev/null || echo '?')"
else
  info "Installing GitHub Copilot CLI globally via npm (requires npm in PATH)"
  # Use npm from current node/nvm installation
  if command -v npm >/dev/null 2>&1; then
    npm install -g @github/copilot --no-fund --no-audit
    info "copilot version: $(copilot --version 2>/dev/null || echo 'installed')"
  else
    err "npm is not available. Ensure nvm/node install succeeded and npm is in PATH."
    exit 1
  fi
fi

info "Installation complete."

cat <<'EOF'
Next steps:
- Open a new terminal (or `source ~/.nvm/nvm.sh`) so nvm/node are on your PATH in interactive shells.
- To authenticate gh: run `gh auth login` and follow instructions.
- To authenticate copilot CLI: run `copilot auth login` (it may open a browser or print a code to paste).

Run now (example):
  source ~/.nvm/nvm.sh
  gh --version
  copilot --version
EOF

exit 0

