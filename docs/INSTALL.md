# Setup Guide

## What you need

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | Uses `match/case` syntax |
| A Telegram bot token | Create one via [@BotFather](https://t.me/BotFather) — free, takes 2 min |
| Your Telegram chat ID | Get it from [@userinfobot](https://t.me/userinfobot) |
| Claude CLI | [Install here](https://claude.ai/code) — must be authenticated |
| Cursor Agent | Optional — leave blank to use Claude for everything |

---

## Quick setup (recommended)

Clone the repo and run the install script. It handles everything interactively:

```bash
git clone https://github.com/YOUR_USERNAME/ai-cli-anywhere.git
cd ai-cli-anywhere
bash scripts/install.sh
```

The script will:
- Check your Python version
- Create a virtual environment and install dependencies
- Walk you through creating a Telegram bot step by step
- Help you find your chat ID
- Check if Claude CLI and Cursor are available
- Write your `.env` file
- Optionally set up a systemd service so the bot runs on startup (Linux)

---

## Manual setup

If you prefer to do it yourself:

### 1. Create your Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a name (shown in chat, e.g. `My Dev Assistant`)
4. Choose a username (must end in `_bot`, e.g. `mydevassistant_bot`)
5. BotFather gives you a token — copy it. Format: `123456789:ABCdef...`

### 2. Get your chat ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It replies with your numeric ID (e.g. `987654321`)
3. This is your `ALLOWED_CHAT_ID` — only this account can talk to your bot

### 3. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configure

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
ALLOWED_CHAT_ID=987654321
```

See `.env.example` for all options with descriptions.

### 5. Run

```bash
./scripts/run.sh
```

---

## Running on a server (always-on, no laptop needed)

If you want the bot available 24/7 without keeping your machine on, run it on a free cloud VM.

**Oracle Cloud free tier** gives you 2 Linux VMs permanently free — no credit card tricks, genuinely free:

1. Sign up at [cloud.oracle.com](https://cloud.oracle.com)
2. Create an **Always Free** VM (Ubuntu, 1 OCPU, 1GB RAM)
3. SSH in and follow the manual setup above
4. Clone your own projects onto the VM — Claude CLI and Cursor will have access to them

The install script's systemd setup step keeps the bot running even after reboots.

---

## Routing

| Message | Goes to |
|---------|---------|
| Contains `@claude`, `claude:`, `hey claude` | Claude CLI |
| Everything else | Cursor Agent |
| `CURSOR_CLI_PATH` is blank | Claude CLI for everything |

Patterns are fully configurable via `CLAUDE_PATTERNS` in `.env`.

---

## Switching models

Send `/model` in your Telegram chat at any time:

```
/model claude opus       → switch Claude to Opus
/model claude sonnet     → switch Claude to Sonnet
/model claude haiku      → switch Claude to Haiku
/model cursor sonnet 4.5 → switch Cursor model (forwarded natively)
/model                   → show usage
```

Aliases are defined in `.env` under `CLAUDE_MODEL_ALIASES`. When Anthropic releases new versions, just update that line and restart — no code changes needed.

---

## Troubleshooting

**"TELEGRAM_BOT_TOKEN must be set"**
→ Copy `.env.example` to `.env` and fill in your token.

**"ALLOWED_CHAT_ID must be set"**
→ Get your ID from [@userinfobot](https://t.me/userinfobot) and set it in `.env`.

**Bot doesn't respond**
→ Check `ALLOWED_CHAT_ID` — must be your exact numeric Telegram user ID.
→ Make sure you're messaging the right bot (the one whose token is in `.env`).

**"agent: command not found"**
→ Cursor isn't installed or not in PATH. Set `CURSOR_CLI_PATH=` (blank) to use Claude only.

**"claude: command not found"**
→ Install Claude CLI from [claude.ai/code](https://claude.ai/code) and ensure it's in PATH.

**Python version error**
→ Run `python3 --version`. Requires Python 3.10+.

---

## Session persistence

Conversation context is maintained per user automatically:

| File | Contents |
|------|----------|
| `.claude_session_ids.json` | Claude CLI `--resume` session IDs |
| `.cursor_chat_ids.json` | Cursor Agent chat IDs |

All these files are gitignored — they stay on your machine only.
