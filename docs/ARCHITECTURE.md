# Architecture

## Overview

Pure Python async bot that bridges the Telegram Bot API with Claude CLI and Cursor Agent.

```
Telegram (phone)
      │
      ▼
 Telegram Bot API  (python-telegram-bot, long-polling)
      │
      ▼
 src/telegram/client.py   ← receives updates, filters by chat ID, manages typing
      │
      ▼
 src/router.py            ← routing decisions, session management
      │
      ├─── @claude tag? ──► Claude CLI (subprocess)
      │
      └─── default ───────► Cursor Agent (subprocess)
```

## Components

### `src/main.py`
Entry point. Wires `Config → TelegramClient → MessageRouter` and calls `client.run()`.

### `src/telegram/client.py` — `TelegramClient`
Event-driven Telegram transport.
- Registers a message handler with `python-telegram-bot`'s `Application`
- Filters incoming updates by `ALLOWED_CHAT_ID` (digit-normalized)
- Converts `Update → ChatMessage` (reuses existing data type)
- Spawns `TelegramTypingIndicator` while the router processes
- Sends the response back via `bot.send_message()`

### `src/telegram/typing.py` — `TelegramTypingIndicator`
Keeps the Telegram "typing…" indicator alive while AI processes.
- Calls `send_chat_action(TYPING)` every 4 s (action expires after ~5 s)
- Runs as an `asyncio.Task`; cancelled via `asyncio.Event` when done

### `src/router.py` — `MessageRouter`
Pure routing logic, transport-agnostic.
- `handle(message)` — decides Claude vs Cursor, returns reply string
- `_call_claude_cli()` — manages `--resume` session IDs (JSON output on first call)
- `_call_cursor_cli()` — manages Cursor chat IDs (creates chat on first message)

### `src/bot_client.py`
Abstract interfaces (`BotClient`, `TypingIndicator`). Transport layer must implement these.

### `src/config.py`
Frozen dataclass loaded from `.env`. Single source of truth for all runtime config.
Validated on startup — fails fast if `TELEGRAM_BOT_TOKEN` or `ALLOWED_CHAT_ID` is missing.

### `src/constants.py`
All magic values: typing interval, CLI flags, log message strings.
No inline literals anywhere else in the codebase.

### `src/message_handler.py`
Stateless filtering. `MessageHandler.filter_messages()` keeps only messages from the allowed ID (digit-normalized comparison).

### `src/chat_store.py`
JSON-backed persistence for conversation sessions.
- `ChatStore` — base (load/save JSON)
- `ClaudeSessionStore` — Claude CLI `--resume` IDs per sender
- `ProcessedMessageStore` — deduplication; last message per sender

## Message Routing

| Trigger | Destination |
|---------|------------|
| `/model claude <alias>` | Sets Claude model (resolves alias from `CLAUDE_MODEL_ALIASES`) |
| `/model cursor <name>` | Forwards `/model <name>` to Cursor Agent |
| `@claude`, `claude:`, `hey claude`, `claude,` | Claude CLI |
| Everything else | Cursor Agent |
| `CURSOR_CLI_PATH` blank | Claude CLI (all messages) |

Routing patterns configurable via `CLAUDE_PATTERNS` in `.env`.
Model aliases configurable via `CLAUDE_MODEL_ALIASES` in `.env`.

## Principles

- **NO if/else** — `match/case` throughout
- **NO for loops** — `map()`, `filter()`, `next()`, generator expressions
- **NO hard-coded values** — all config from `.env` / `constants.py`
- **NO blocking** — `asyncio` + event-driven Telegram updates
- **TDD** — tests written first

## Data Flow

```
Telegram Update arrives
  └─ TelegramClient._is_allowed(update)      ← ALLOWED_CHAT_ID check
  └─ TelegramClient._update_to_message()     ← Update → ChatMessage
  └─ TelegramTypingIndicator.start()
  └─ MessageRouter.handle(message)
       └─ _is_claude_tagged(content, patterns)
            ├─ True  → _call_claude_cli(sender, stripped_content)
            └─ False → _call_cursor_cli(sender, content)
  └─ TelegramTypingIndicator.stop()
  └─ TelegramClient.send_message(sender, response)
```
