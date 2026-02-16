"""MessageRouter — pure routing logic, transport-agnostic."""
import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from functools import reduce

from src.chat_store import ChatStore, ClaudeSessionStore, MessageHistoryStore
from src.config import Config
from src.constants import (
    CLAUDE_MODEL_FLAG,
    CLAUDE_OUTPUT_FLAG,
    CLAUDE_OUTPUT_FORMAT,
    CLAUDE_PROMPT_FLAG,
    CLAUDE_RESUME_FLAG,
    CURSOR_CREATE_CHAT,
    CURSOR_PROMPT_FLAG,
    CURSOR_RESUME_FLAG,
    CURSOR_TRUST_FLAG,
    MSG_CLAUDE_TIMEOUT,
    MSG_CURSOR_TIMEOUT,
    MSG_ERR_NO_CURSOR,
    MSG_ERR_NO_CURSOR_RESPONSE,
    MSG_ERR_TIMEOUT,
    CLAUDE_STREAM_FORMAT,
    CMD_HISTORY,
    HISTORY_MAX_ENTRIES,
    MSG_HISTORY_BOT,
    MSG_HISTORY_EMPTY,
    MSG_HISTORY_HEADER,
    MSG_HISTORY_YOU,
    MSG_MODEL_SET_CLAUDE,
    MSG_MODEL_USAGE,
    MSG_NEW_SESSION,
    MSG_ROUTING_CLAUDE,
    MSG_ROUTING_CURSOR,
    MSG_STATUS,
)
from src.message_handler import ChatMessage, normalize_phone

logger = logging.getLogger(__name__)


# ── pure helpers (module-level so tests can import them directly) ──────────────


def _is_claude_tagged(message: str, patterns: tuple[str, ...]) -> bool:
    return any(p in message.lower() for p in patterns)


def _strip_claude_tag(message: str, patterns: tuple[str, ...]) -> str:
    return reduce(
        lambda text, p: text.replace(p, "").replace(p.upper(), ""),
        patterns,
        message,
    ).strip()


def match_model_args(model: str | None) -> list[str]:
    """Return --model <id> args when a model is set, else empty list."""
    match model:
        case str() as m if m:
            return [CLAUDE_MODEL_FLAG, m]
        case _:
            return []


# ── router ────────────────────────────────────────────────────────────────────


class MessageRouter:
    """Routes incoming messages to Claude CLI or Cursor Agent and returns the reply."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._chat_store = ChatStore()
        self._claude_store = ClaudeSessionStore()
        self._history_store = MessageHistoryStore(max_per_sender=HISTORY_MAX_ENTRIES * 2)
        self._claude_model: str | None = None

    # ── model state ───────────────────────────────────────────────────────────

    def get_claude_model(self) -> str | None:
        return self._claude_model

    def set_claude_model(self, model: str) -> None:
        self._claude_model = model

    async def handle_model_command(self, sender: str, provider: str, args: str) -> str:
        match provider.lower():
            case "claude":
                raw = args.strip()
                resolved = self._config.claude_model_aliases.get(raw.lower(), raw)
                self._claude_model = resolved
                return MSG_MODEL_SET_CLAUDE % resolved
            case "cursor":
                return await self._call_cursor_cli(sender, "/model " + args.strip())
            case _:
                return MSG_MODEL_USAGE

    def handle_status_command(self) -> str:
        model = self._claude_model or "default"
        voice = "enabled" if self._config.openai_api_key else "disabled"
        cursor = self._config.cursor_cli_path or "not configured"
        return MSG_STATUS % (model, voice, cursor)

    def handle_history_command(self, sender: str) -> str:
        entries = self._history_store.get(sender)
        match entries:
            case []:
                return MSG_HISTORY_EMPTY
            case history:
                lines = [MSG_HISTORY_HEADER % len(history)]
                lines += list(map(
                    lambda e: (MSG_HISTORY_YOU if e.role == "you" else MSG_HISTORY_BOT) % e.content,
                    history,
                ))
                return "\n".join(lines)

    def handle_new_command(self, sender: str) -> str:
        key = normalize_phone(sender)
        self._claude_store.delete(key)
        self._chat_store.delete(key)
        self._history_store.delete(sender)
        return MSG_NEW_SESSION

    async def handle(self, message: ChatMessage, **_) -> str:
        use_claude = (
            _is_claude_tagged(message.content, self._config.claude_patterns)
            or not self._config.cursor_cli_path
        )
        self._history_store.append(message.sender, "you", message.content)
        match use_claude:
            case True:
                logger.info(MSG_ROUTING_CLAUDE)
                response = await self._call_claude_cli(
                    message.sender,
                    _strip_claude_tag(message.content, self._config.claude_patterns),
                )
            case False:
                logger.info(MSG_ROUTING_CURSOR)
                response = await self._call_cursor_cli(message.sender, message.content)
        self._history_store.append(message.sender, "bot", response)
        return response

    async def stream_handle(self, message: ChatMessage) -> AsyncGenerator[str, None]:
        """Yields accumulated text chunks as Claude responds. Cursor routes fall back to one chunk."""
        use_claude = (
            _is_claude_tagged(message.content, self._config.claude_patterns)
            or not self._config.cursor_cli_path
        )
        self._history_store.append(message.sender, "you", message.content)
        match use_claude:
            case True:
                logger.info(MSG_ROUTING_CLAUDE)
                full_text = ""
                async for chunk in self._stream_claude_cli(
                    message.sender,
                    _strip_claude_tag(message.content, self._config.claude_patterns),
                ):
                    full_text = chunk
                    yield chunk
                self._history_store.append(message.sender, "bot", full_text)
            case False:
                logger.info(MSG_ROUTING_CURSOR)
                response = await self._call_cursor_cli(message.sender, message.content)
                self._history_store.append(message.sender, "bot", response)
                yield response

    async def _stream_claude_cli(self, sender: str, message: str) -> AsyncGenerator[str, None]:
        key = normalize_phone(sender)
        session_id = self._claude_store.get(key)
        claude = self._config.claude_cli_path

        base_args = (
            [claude, CLAUDE_PROMPT_FLAG, message, CLAUDE_RESUME_FLAG, session_id]
            if session_id
            else [claude, CLAUDE_PROMPT_FLAG, message, CLAUDE_OUTPUT_FLAG, CLAUDE_STREAM_FORMAT]
        )
        args = base_args + match_model_args(self._claude_model)

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            if not process.stdout:
                yield "Error: No stdout from Claude process"
                return
            
            accumulated = ""
            async for raw_line in process.stdout:
                line = raw_line.decode(errors="replace").strip()
                match line:
                    case "":
                        continue
                    case _:
                        pass
                try:
                    event = json.loads(line)
                    match event.get("type"):
                        case "assistant":
                            content = event.get("message", {}).get("content", [])
                            text = "".join(
                                b.get("text", "") for b in content if b.get("type") == "text"
                            )
                            match text.strip():
                                case "":
                                    pass
                                case t:
                                    accumulated += t
                                    yield accumulated
                        case "result":
                            new_id = event.get("session_id")
                            match new_id:
                                case str() as s if s:
                                    self._claude_store.set(key, s)
                                case _:
                                    pass
                            final = event.get("result", "").strip()
                            match final:
                                case "" | None:
                                    pass
                                case r if r != accumulated.strip():
                                    yield r
                        case _:
                            pass
                except (json.JSONDecodeError, TypeError):
                    accumulated += line + "\n"
                    yield accumulated.strip()

            await process.wait()
            match (process.returncode, accumulated):
                case (0, _):
                    pass
                case (_, _):
                    if process.stderr:
                        err = (await process.stderr.read()).decode()[:100]
                        yield f"Error calling Claude: {err}"
                    else:
                        yield "Error calling Claude"

        except asyncio.TimeoutError:
            yield MSG_ERR_TIMEOUT
        except Exception as exc:
            logger.error("Error streaming Claude: %s", exc)
            yield f"Error: {exc}"

    async def _call_claude_cli(self, sender: str, message: str) -> str:
        try:
            key = normalize_phone(sender)
            session_id = self._claude_store.get(key)
            claude = self._config.claude_cli_path

            base_args = (
                [claude, CLAUDE_PROMPT_FLAG, message, CLAUDE_RESUME_FLAG, session_id]
                if session_id
                else [claude, CLAUDE_PROMPT_FLAG, message, CLAUDE_OUTPUT_FLAG, CLAUDE_OUTPUT_FORMAT]
            )
            model_args = match_model_args(self._claude_model)
            args = base_args + model_args

            logger.info("Calling Claude CLI…")
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self._config.claude_timeout
            )

            match process.returncode:
                case 0:
                    pass
                case _:
                    err = stderr.decode()[:100] if stderr else "Unknown error"
                    logger.error("Claude CLI error: %s", err)
                    return f"Error calling Claude: {err}"

            match session_id:
                case str() if session_id:
                    return stdout.decode().strip() if stdout else ""
                case _:
                    try:
                        data = json.loads(stdout.decode()) if stdout else {}
                        new_id = data.get("session_id")
                        match new_id:
                            case str() if new_id:
                                self._claude_store.set(key, new_id)
                            case _:
                                pass
                        return (data.get("result") or "").strip()
                    except (json.JSONDecodeError, TypeError):
                        return stdout.decode().strip() if stdout else ""

        except asyncio.TimeoutError:
            logger.error(MSG_CLAUDE_TIMEOUT)
            return MSG_ERR_TIMEOUT
        except Exception as exc:
            logger.error("Error calling Claude: %s", exc)
            return f"Error: {exc}"

    async def _call_cursor_cli(self, sender: str, message: str) -> str:
        cursor = self._config.cursor_cli_path
        if cursor is None:
            return MSG_ERR_NO_CURSOR
        try:
            key = normalize_phone(sender)
            chat_id = self._chat_store.get(key)

            cwd = self._config.cursor_working_dir
            match chat_id:
                case None | "":
                    create = await asyncio.create_subprocess_exec(
                        cursor,
                        CURSOR_CREATE_CHAT,
                        CURSOR_TRUST_FLAG,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=cwd,
                    )
                    stdout, _ = await asyncio.wait_for(create.communicate(), timeout=10)
                    new_chat_id = stdout.decode().strip() if stdout else ""
                    match (create.returncode, new_chat_id):
                        case (0, id_val) if id_val:
                            self._chat_store.set(key, id_val)
                            chat_id = id_val
                        case _:
                            chat_id = None
                case _:
                    pass

            args = (
                [cursor, CURSOR_TRUST_FLAG, CURSOR_PROMPT_FLAG, message, CURSOR_RESUME_FLAG, chat_id]
                if chat_id
                else [cursor, CURSOR_TRUST_FLAG, CURSOR_PROMPT_FLAG, message]
            )

            logger.info("Calling Cursor Agent…")
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self._config.cursor_timeout
            )

            response = stdout.decode().strip() if stdout else ""
            match (process.returncode, response):
                case (0, resp) if resp:
                    return resp
                case (0, _):
                    return MSG_ERR_NO_CURSOR_RESPONSE
                case _:
                    err = stderr.decode()[:200] if stderr else "Unknown error"
                    logger.error("Cursor Agent failed: %s", err)
                    return f"Error: {err}"

        except asyncio.TimeoutError:
            logger.error(MSG_CURSOR_TIMEOUT, self._config.cursor_timeout)
            return MSG_ERR_TIMEOUT
        except Exception as exc:
            logger.error("Error calling Cursor Agent: %s", exc)
            return f"Error: {exc}"
