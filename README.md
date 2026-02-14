# ai-cli-anywhere

Use your Claude CLI and Cursor Agent from your phone via Telegram.

Built this for myself — tired of being away from my desk and not being able to continue a session with my AI tools. No cloud API, no walled garden. The AI runs on your machine (or a free cloud VM), with access to your actual projects.

## How it works

```
Your Telegram message
        ↓
Telegram Bot API  (official, event-driven)
        ↓
  @claude tag? → Claude CLI (your installation, your projects)
  /model ...   → switch AI model
  everything else → Cursor Agent
        ↓
Reply back to Telegram
```

Conversation memory is persistent across sessions. The bot knows what you talked about yesterday.

## Setup

```bash
git clone https://github.com/idan3011/ai-cli-anywhere.git
cd ai-cli-anywhere
bash scripts/install.sh
```

The script walks you through everything — Telegram bot creation, config, and optionally setting up a systemd service so it runs on startup.

Full guide: [docs/INSTALL.md](./docs/INSTALL.md)

## Running 24/7 without your laptop

Run it on [Oracle Cloud's free tier](https://cloud.oracle.com) — 2 Linux VMs, permanently free.
Clone your projects there, install Claude CLI and Cursor, run the install script. Your dev tools are then available from your phone at any time.

## Switching models

Send `/model` in chat:

```
/model claude opus       → Claude Opus
/model claude sonnet     → Claude Sonnet
/model cursor sonnet 4.5 → Cursor model switch (forwarded natively)
```

When Anthropic releases new versions, update one line in `.env` — no code changes:

```env
CLAUDE_MODEL_ALIASES=opus:claude-opus-4-6,sonnet:claude-sonnet-4-5-20250929,haiku:claude-haiku-4-5-20251001
```

## Requirements

- Python 3.10+
- Claude CLI ([install](https://claude.ai/code))
- Cursor Agent (optional — leave blank to use Claude for everything)
- A Telegram bot token ([@BotFather](https://t.me/BotFather), free, 2 min)

## Docs

- [Setup guide](./docs/INSTALL.md) — step by step, includes Oracle Cloud VM option
- [Architecture](./docs/ARCHITECTURE.md) — how it's built

## License

Copyright (c) 2026. All Rights Reserved. See [LICENSE](./LICENSE).
