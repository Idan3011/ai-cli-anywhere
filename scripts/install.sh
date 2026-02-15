#!/usr/bin/env bash
# ai-cli-anywhere — interactive setup
# Walks you through everything and writes your .env automatically.

set -e

# ── colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}→ $*${RESET}"; }
success() { echo -e "${GREEN}✓ $*${RESET}"; }
warn()    { echo -e "${YELLOW}! $*${RESET}"; }
error()   { echo -e "${RED}✗ $*${RESET}"; exit 1; }
header()  { echo -e "\n${BOLD}── $* ──────────────────────────────────────${RESET}"; }
pause()   { read -rp "$(echo -e "${CYAN}Press Enter to continue...${RESET}")"; }

# ── script dir ────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo -e "\n${BOLD}ai-cli-anywhere — setup wizard${RESET}"
echo "This will walk you through everything and write your .env automatically."
echo ""

# ── 1. Python ─────────────────────────────────────────────────────────────────
header "1. Python"
PYTHON=$(command -v python3 || command -v python || true)
[ -z "$PYTHON" ] && error "Python not found. Install Python 3.10+ and try again."

PY_MAJOR=$("$PYTHON" -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$("$PYTHON" -c 'import sys; print(sys.version_info.minor)')
PY_VERSION="${PY_MAJOR}.${PY_MINOR}"

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    error "Python 3.10+ required (you have $PY_VERSION). Please upgrade and retry."
fi
success "Python $PY_VERSION"

# ── 2. Dependencies ───────────────────────────────────────────────────────────
header "2. Installing dependencies"
if [ ! -d "venv" ]; then
    info "Creating virtual environment..."
    "$PYTHON" -m venv venv
fi
source venv/bin/activate
info "Installing packages..."
pip install -r requirements.txt -q
success "Dependencies ready"

# ── 3. Telegram bot token ─────────────────────────────────────────────────────
header "3. Telegram bot token"
echo ""
echo "  You need a bot from @BotFather. Here's how:"
echo ""
echo "  1. Open Telegram"
echo "  2. Search for @BotFather and open it"
echo "  3. Send:  /newbot"
echo "  4. Enter a display name  (e.g.  My Dev Assistant)"
echo "  5. Enter a username      (must end in _bot,  e.g.  mydev_bot)"
echo "  6. BotFather sends you a token — copy it"
echo ""
echo "  Once you have the token, paste it below."
echo ""

while true; do
    read -rp "$(echo -e "${BOLD}Bot token:${RESET} ")" BOT_TOKEN
    if [[ "$BOT_TOKEN" =~ ^[0-9]+:.{20,}$ ]]; then
        success "Token accepted"
        break
    fi
    warn "Doesn't look right. Expected format: 123456789:ABCdefGhIJKlm..."
done

# ── 4. Chat ID ────────────────────────────────────────────────────────────────
header "4. Your Telegram chat ID"
echo ""
echo "  Your chat ID is a number that identifies your Telegram account."
echo "  Only this account will be allowed to talk to the bot."
echo ""
echo "  1. Open Telegram"
echo "  2. Search for @userinfobot and open it"
echo "  3. Send any message to it"
echo "  4. It replies with your numeric ID — copy it"
echo ""
echo "  Paste it below."
echo ""

while true; do
    read -rp "$(echo -e "${BOLD}Chat ID:${RESET} ")" CHAT_ID
    if [[ "$CHAT_ID" =~ ^-?[0-9]+$ ]]; then
        success "Chat ID: $CHAT_ID"
        break
    fi
    warn "Chat ID must be a number (e.g. 987654321)"
done

# ── 5. Claude CLI ─────────────────────────────────────────────────────────────
header "5. Claude CLI"
echo ""
CLAUDE_PATH="claude"

if command -v claude &>/dev/null; then
    CLAUDE_PATH="$(command -v claude)"
    success "Found claude at $CLAUDE_PATH"
    echo ""
    echo "  IMPORTANT: Claude CLI must be authenticated before the bot can use it."
    echo "  If you haven't logged in yet:"
    echo ""
    echo "    Open a new terminal and run:  claude login"
    echo ""
    echo "  Come back here once that's done."
    echo ""
    pause
else
    warn "claude not found in PATH"
    echo ""
    echo "  Install it from: https://claude.ai/code"
    echo "  Then run:  claude login"
    echo ""
    echo "  Once installed and logged in, come back and re-run this script."
    echo "  Or enter a custom path if it's installed somewhere unusual:"
    echo ""
    read -rp "$(echo -e "${BOLD}Path to claude (Enter to skip):${RESET} ")" CUSTOM_PATH
    CLAUDE_PATH="${CUSTOM_PATH:-claude}"
    warn "Remember to run 'claude login' before starting the bot"
fi

# ── 6. Cursor Agent ───────────────────────────────────────────────────────────
header "6. Cursor Agent (optional)"
echo ""
echo "  Cursor Agent routes messages to your Cursor IDE's AI."
echo "  Without it, all messages go to Claude."
echo ""
CURSOR_PATH=""
CURSOR_WORKING_DIR=""

if command -v agent &>/dev/null; then
    CURSOR_PATH="agent"
    success "Found Cursor agent at $(command -v agent)"
    echo ""
    echo "  Which directory should Cursor work on?"
    echo "  This should be the root of your project — Cursor will have access to those files."
    echo ""
    read -rp "$(echo -e "${BOLD}Project directory path (Enter for current dir):${RESET} ")" CURSOR_WORKING_DIR
    if [ -n "$CURSOR_WORKING_DIR" ]; then
        if [ -d "$CURSOR_WORKING_DIR" ]; then
            success "Cursor will work in: $CURSOR_WORKING_DIR"
        else
            warn "Directory not found — double-check the path after setup"
        fi
    else
        info "Cursor will use the directory the bot is started from"
    fi
else
    warn "agent not found in PATH"
    echo ""
    read -rp "$(echo -e "${BOLD}Do you want to configure Cursor anyway? [y/N]:${RESET} ")" USE_CURSOR
    if [[ "$USE_CURSOR" =~ ^[Yy]$ ]]; then
        read -rp "$(echo -e "${BOLD}Path to agent binary:${RESET} ")" CURSOR_PATH
        read -rp "$(echo -e "${BOLD}Project directory path (Enter for current dir):${RESET} ")" CURSOR_WORKING_DIR
    else
        info "Skipping Cursor — all messages will go to Claude"
    fi
fi

# ── 7. Write .env ─────────────────────────────────────────────────────────────
header "7. Writing .env"

WRITE_ENV=true
if [ -f ".env" ]; then
    echo ""
    read -rp "$(echo -e "${BOLD}.env already exists. Overwrite it? [y/N]:${RESET} ")" OVERWRITE
    [[ "$OVERWRITE" =~ ^[Yy]$ ]] || WRITE_ENV=false
fi

if [ "$WRITE_ENV" = true ]; then
    cat > .env <<EOF
# Telegram
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
ALLOWED_CHAT_ID=${CHAT_ID}

# AI Routing
CLAUDE_CLI_PATH=${CLAUDE_PATH}
CLAUDE_TIMEOUT=45
CURSOR_CLI_PATH=${CURSOR_PATH}
CURSOR_TIMEOUT=60
CURSOR_WORKING_DIR=${CURSOR_WORKING_DIR}
CLAUDE_PATTERNS=@claude,claude:,hey claude,claude,

# Model aliases — update right-hand side when Anthropic releases new versions
CLAUDE_MODEL_ALIASES=opus:claude-opus-4-6,sonnet:claude-sonnet-4-5-20250929,haiku:claude-haiku-4-5-20251001

# Logging
LOG_LEVEL=INFO
EOF
    success ".env written"
else
    info "Keeping existing .env"
fi

# ── 8. Systemd service (Linux only) ───────────────────────────────────────────
if [ "$(uname -s)" = "Linux" ] && command -v systemctl &>/dev/null; then
    header "8. Run on startup (systemd)"
    echo ""
    echo "  A systemd service keeps the bot alive after reboots automatically."
    echo ""
    read -rp "$(echo -e "${BOLD}Set up systemd service? [y/N]:${RESET} ")" SETUP_SYSTEMD
    if [[ "$SETUP_SYSTEMD" =~ ^[Yy]$ ]]; then
        SERVICE_NAME="ai-cli-anywhere"
        SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

        sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=ai-cli-anywhere Telegram bot
After=network.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${PROJECT_DIR}/.env
Environment=PYTHONPATH=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python3 -m src.main
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        sudo systemctl enable "$SERVICE_NAME"
        sudo systemctl start "$SERVICE_NAME"
        success "Service installed and started"
        info "Check status: systemctl status $SERVICE_NAME"
        info "View logs:    journalctl -u $SERVICE_NAME -f"
    fi
fi

# ── done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}────────────────────────────────────────${RESET}"
echo -e "${GREEN}${BOLD}Setup complete!${RESET}"
echo ""
echo "  Start the bot:"
echo "    ./scripts/run.sh"
echo ""
echo "  Then open Telegram, message your bot, and it should respond."
echo "  Send /help inside the chat to see all available commands."
echo ""
