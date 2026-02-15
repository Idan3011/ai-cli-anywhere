import json
import logging
from pathlib import Path

from src.message_handler import normalize_phone

logger = logging.getLogger(__name__)

DEFAULT_STORE_PATH = Path(".cursor_chat_ids.json")
CLAUDE_STORE_PATH = Path(".claude_session_ids.json")
MESSAGE_STORE_PATH = Path(".processed_messages.json")


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


class ClaudeSessionStore(ChatStore):

    def __init__(self, path: Path = CLAUDE_STORE_PATH):
        super().__init__(path)


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
