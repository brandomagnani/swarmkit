#!/bin/bash
# Setup script for agent-browser
# Smart installation - skips already-installed components

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_ok() { echo -e "${GREEN}✓${NC} $1"; }
log_skip() { echo -e "${YELLOW}→${NC} $1 (skipped)"; }

# ---------------------------------------------------------------------------
# Check: npm available
# ---------------------------------------------------------------------------
if ! command -v npm &> /dev/null; then
    echo "Error: npm is required but not installed."
    echo "Install Node.js from https://nodejs.org/"
    exit 1
fi

# ---------------------------------------------------------------------------
# Check: agent-browser CLI installed
# ---------------------------------------------------------------------------
if command -v agent-browser &> /dev/null; then
    log_skip "agent-browser already installed: $(which agent-browser)"
else
    echo "Installing agent-browser..."
    npm install -g agent-browser
    log_ok "agent-browser installed"
fi

# ---------------------------------------------------------------------------
# Check: Playwright Chromium installed
# Checks both Linux (~/.cache) and macOS (~/Library/Caches) locations
# ---------------------------------------------------------------------------
is_chromium_installed() {
    local linux_cache="${HOME}/.cache/ms-playwright"
    local macos_cache="${HOME}/Library/Caches/ms-playwright"

    # Check Linux location
    if [[ -d "$linux_cache" ]] && ls "$linux_cache" 2>/dev/null | grep -q "^chromium"; then
        return 0
    fi

    # Check macOS location
    if [[ -d "$macos_cache" ]] && ls "$macos_cache" 2>/dev/null | grep -q "^chromium"; then
        return 0
    fi

    return 1
}

if is_chromium_installed; then
    log_skip "Playwright Chromium already installed"
else
    echo "Installing Playwright Chromium..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Linux detected - including system dependencies..."
        agent-browser install --with-deps
    else
        agent-browser install
    fi
    log_ok "Playwright Chromium installed"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
log_ok "Setup complete. agent-browser is ready to use."
