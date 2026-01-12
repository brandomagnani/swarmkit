#!/bin/bash
# Setup script for agent-browser
# Smart installation - installs in skill directory, works from anywhere

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_ok() { echo -e "${GREEN}✓${NC} $1"; }
log_skip() { echo -e "${YELLOW}→${NC} $1 (skipped)"; }

# Get the skill directory (parent of scripts/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# ---------------------------------------------------------------------------
# Check: npm available
# ---------------------------------------------------------------------------
if ! command -v npm &> /dev/null; then
    echo "Error: npm is required but not installed."
    echo "Install Node.js from https://nodejs.org/"
    exit 1
fi

# ---------------------------------------------------------------------------
# Install: agent-browser in skill directory
# ---------------------------------------------------------------------------
cd "$SKILL_DIR"

if [[ -d "node_modules/agent-browser" ]]; then
    log_skip "agent-browser already installed in skill directory"
else
    echo "Installing agent-browser in $SKILL_DIR..."
    npm install agent-browser
    log_ok "agent-browser installed"
fi

# ---------------------------------------------------------------------------
# Create wrapper script that runs from skill directory
# ---------------------------------------------------------------------------
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/agent-browser" << EOF
#!/bin/bash
cd "$SKILL_DIR" && npx agent-browser "\$@"
EOF
chmod +x "$HOME/.local/bin/agent-browser"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
    echo "Note: Add ~/.local/bin to your PATH for future sessions"
fi

log_ok "Wrapper created at ~/.local/bin/agent-browser"

# ---------------------------------------------------------------------------
# Check: Playwright Chromium installed
# ---------------------------------------------------------------------------
is_chromium_installed() {
    local linux_cache="${HOME}/.cache/ms-playwright"
    local macos_cache="${HOME}/Library/Caches/ms-playwright"

    if [[ -d "$linux_cache" ]] && ls "$linux_cache" 2>/dev/null | grep -q "^chromium"; then
        return 0
    fi
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
        npx agent-browser install --with-deps
    else
        npx agent-browser install
    fi
    log_ok "Playwright Chromium installed"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
log_ok "Setup complete. Run 'agent-browser' from anywhere."
