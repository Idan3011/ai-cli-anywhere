import json
import logging
from pathlib import Path
from typing import NamedTuple

from src.message_handler import normalize_phone

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = Path(".cursor_chat_ids.json")
CLAUDE_STORE_PATH = Path(".claude_session_ids.json")
MESSAGE_STORE_PATH = Path(".processed_messages.json")
HISTORY_STORE_PATH = Path(".message_history.json")


class ChatStore:

    def __init__(self, path: Path = DEFAULT_STORE_PATH):
        self._path = path
        self._store: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        match self._path.exists():
            case True:
                try:
                    with open(self._path) as f:
                        raw = json.load(f)
                    self._store = dict(
                        map(lambda kv: (normalize_phone(kv[0]) or kv[0], kv[1]), raw.items())
                    )
                    match self._store != raw:
                        case True:
                            self._save()
                            logger.info(f"Migrated {self._path.name}: normalized store keys")
                        case False:
                            pass
                except Exception as e:
                    logger.warning(f"Store load failed: {e}, starting fresh")
            case False:
                pass

    def _save(self) -> None:
        try:
            with open(self._path, "w") as f:
                json.dump(self._store, f, indent=2)
        except Exception as e:
            logger.warning(f"Store save failed: {e}")

    def get(self, sender: str) -> str | None:
        return self._store.get(sender)

    def set(self, sender: str, value: str) -> None:
        self._store[sender] = value
        self._save()

    def delete(self, sender: str) -> None:
        match self._store.pop(sender, None):
            case None:
                pass
            case _:
                self._save()


class ClaudeSessionStore(ChatStore):

    def __init__(self, path: Path = CLAUDE_STORE_PATH):
        super().__init__(path)


class HistoryEntry(NamedTuple):
    role: str
    content: str


class MessageHistoryStore:

    def __init__(self, path: Path = HISTORY_STORE_PATH, max_per_sender: int = 20) -> None:
        self._path = path
        self._max = max_per_sender
        self._store: dict[str, list[dict]] = {}
        self._load()

    def _load(self) -> None:
        match self._path.exists():
            case True:
                try:
                    with open(self._path) as f:
                        self._store = json.load(f)
                except Exception as e:
                    logger.warning("History load failed: %s, starting fresh", e)
            case False:
                pass

    def _save(self) -> None:
        try:
            with open(self._path, "w") as f:
                json.dump(self._store, f, indent=2)
        except Exception as e:
            logger.warning("History save failed: %s", e)

    def append(self, sender: str, role: str, content: str) -> None:
        key = normalize_phone(sender) or sender
        history = self._store.get(key, [])
        history.append({"role": role, "content": content})
        self._store[key] = history[-self._max:]
        self._save()

    def get(self, sender: str) -> list[HistoryEntry]:
        key = normalize_phone(sender) or sender
        return list(map(lambda e: HistoryEntry(**e), self._store.get(key, [])))

    def delete(self, sender: str) -> None:
        key = normalize_phone(sender) or sender
        match self._store.pop(key, None):
            case None:
                pass
            case _:
                self._save()


class ProcessedMessageStore(ChatStore):

    def __init__(self, path: Path = MESSAGE_STORE_PATH):
        super().__init__(path)

    def is_processed(self, sender: str, content: str) -> bool:
        return self.get(sender) == content

    def mark_processed(self, sender: str, content: str) -> None:
        self.set(sender, content)
        match len(self._store):
            case n if n > 100:
                self._store = dict(list(self._store.items())[-50:])
                self._save()
                logger.info(f"Cleaned up, kept {len(self._store)} recent senders")
            case _:
                pass
