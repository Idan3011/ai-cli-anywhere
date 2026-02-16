"""All magic values live here — no inline literals anywhere else."""

# Telegram typing indicator re-send interval (seconds).
# The TYPING action expires after ~5 s, so we refresh every 4 s.
TELEGRAM_TYPING_INTERVAL: float = 4.0

# Claude CLI flags
CLAUDE_OUTPUT_FORMAT = "json"
CLAUDE_RESUME_FLAG = "--resume"
CLAUDE_OUTPUT_FLAG = "--output-format"
CLAUDE_PROMPT_FLAG = "-p"
CLAUDE_MODEL_FLAG = "--model"

# Cursor CLI flags
CURSOR_CREATE_CHAT = "create-chat"
CURSOR_RESUME_FLAG = "--resume"
CURSOR_PROMPT_FLAG = "-p"
CURSOR_TRUST_FLAG = "--trust"

# Log / user-facing messages
MSG_BOT_STARTING = "Starting Telegram bot…"
MSG_CONNECTED = "Telegram bot connected"
MSG_BLOCKED_CHAT = "Blocked update from chat_id: %s"
MSG_NO_RESPONSE = "No response generated"
MSG_SEND_OK = "✓ Sent (%.1fs)"
MSG_SEND_FAIL = "✗ Send failed (%.1fs)"
MSG_CURSOR_TIMEOUT = "Cursor Agent timeout (%ss)"
MSG_CLAUDE_TIMEOUT = "Claude CLI timeout"
MSG_ROUTING_CLAUDE = "→ Claude CLI"
MSG_ROUTING_CURSOR = "→ Cursor Agent"

# Router error replies
MSG_ERR_TIMEOUT = "Error: Request timed out — try again"
MSG_ERR_NO_CURSOR = "Error: Cursor CLI path not configured"
MSG_ERR_NO_CURSOR_RESPONSE = "Error: No response from Cursor Agent"

# Voice transcription
WHISPER_MODEL = "whisper-1"
VOICE_FILENAME = "voice.ogg"
MSG_VOICE_TRANSCRIPTION_FAILED = "Could not transcribe voice message — please try again"
MSG_VOICE_NOT_CONFIGURED = "Voice messages are not supported in this setup."

# Image analysis
CLAUDE_VISION_MODEL = "claude-opus-4-6"
OPENAI_VISION_MODEL = "gpt-4o"
ALBUM_DEBOUNCE_SECONDS: float = 0.5

# Streaming responses
CLAUDE_STREAM_FORMAT = "stream-json"
STREAM_EDIT_INTERVAL: float = 1.0
MSG_STREAM_PLACEHOLDER = "..."
MSG_IMAGE_DEFAULT_PROMPT = "What do you see in this image? Describe it in detail."
MSG_IMAGE_ANALYSIS_FAILED = "Could not analyze image — please try again."
MSG_IMAGE_NOT_CONFIGURED = "Image analysis is not supported in this setup."

# /model command
CMD_MODEL = "model"
DEFAULT_CLAUDE_MODEL_ALIASES = (
    "opus:claude-opus-4-6,"
    "sonnet:claude-sonnet-4-5-20250929,"
    "haiku:claude-haiku-4-5-20251001"
)
MSG_MODEL_USAGE = (
    "Usage:\n"
    "  /model claude <model-id>  — switch Claude model\n"
    "  /model cursor <name>      — switch Cursor model\n\n"
    "Examples:\n"
    "  /model claude claude-opus-4-6\n"
    "  /model cursor sonnet 4.5"
)
MSG_MODEL_SET_CLAUDE = "Claude model set to: %s"
MSG_MODEL_STATUS = "Current models:\n• Claude: %s\n• Cursor: (use /model cursor <name>)"

CMD_STATUS = "status"
MSG_STATUS = (
    "Status\n"
    "  Claude model : %s\n"
    "  Voice        : %s\n"
    "  Cursor       : %s\n"
)

CMD_NEW = "new"
MSG_NEW_SESSION = "Session cleared — starting fresh."

CMD_HISTORY = "history"
HISTORY_MAX_ENTRIES = 10
MSG_HISTORY_EMPTY = "No history yet — send a message first."
MSG_HISTORY_HEADER = "Last %d exchanges:\n\n"
MSG_HISTORY_YOU = "You: %s"
MSG_HISTORY_BOT = "Bot: %s"

MSG_HELP = (
    "ai-cli-anywhere — your dev tools on Telegram\n"
    "\n"
    "Commands:\n"
    "  /help                    — show this message\n"
    "  /status                  — current config at a glance\n"
    "  /model claude <alias>    — switch Claude model\n"
    "  /model cursor <name>     — switch Cursor model\n"
    "  /new                     — start a fresh Claude session\n"
    "  /history                 — show last exchanges\n"
    "\n"
    "Media:\n"
    "  Voice note               — transcribed then routed automatically\n"
    "  Photo                    — analyzed by Claude Vision then routed\n"
    "  Photo + caption          — caption becomes the analysis question\n"
    "\n"
    "Model aliases (update in .env):\n"
    "  opus   → claude-opus-4-6\n"
    "  sonnet → claude-sonnet-4-5-20250929\n"
    "  haiku  → claude-haiku-4-5-20251001\n"
    "\n"
    "Routing:\n"
    "  @claude / claude: / hey claude → Claude CLI\n"
    "  everything else                → Cursor Agent\n"
)

