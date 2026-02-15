import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.chat_store import ChatStore, ClaudeSessionStore, ProcessedMessageStore


# --- Helpers ---

def _make_store(tmp_path: Path, data: dict) -> ChatStore:
    p = tmp_path / "store.json"
    p.write_text(json.dumps(data))
    return ChatStore(path=p)


# --- Migration tests ---

def test_load_normalizes_bidi_key(tmp_path):
    """Old bidi-marker key (e.g. from phone number copy-paste) is normalized to digits on load."""
    old_key = "\u2066+972 54-683-8910\u2069"
    store = _make_store(tmp_path, {old_key: "session-abc"})
    assert store.get("972546838910") == "session-abc"
    assert store.get(old_key) is None


def test_load_migrated_file_is_saved(tmp_path):
    """Migrated keys are persisted so the file stays normalized."""
    old_key = "\u2066+972 54-683-8910\u2069"
    p = tmp_path / "store.json"
    p.write_text(json.dumps({old_key: "session-abc"}))
    ChatStore(path=p)
    reloaded = json.loads(p.read_text())
    assert "972546838910" in reloaded
    assert old_key not in reloaded


def test_load_keeps_newer_session_on_key_collision(tmp_path):
    """When old-format and new-format both normalize to same key, new-format value wins."""
    old_key = "\u2066+972 54-683-8910\u2069"
    new_key = "972546838910"
    store = _make_store(tmp_path, {old_key: "old-session", new_key: "new-session"})
    assert store.get(new_key) == "new-session"


def test_load_already_normalized_keys_unchanged(tmp_path):
    """Already-normalized keys load without alteration."""
    store = _make_store(tmp_path, {"972546838910": "session-xyz"})
    assert store.get("972546838910") == "session-xyz"


def test_load_missing_file_starts_empty(tmp_path):
    """Missing file produces empty store without error."""
    store = ChatStore(path=tmp_path / "nonexistent.json")
    assert store.get("972546838910") is None


def test_load_corrupt_file_starts_empty(tmp_path):
    """Corrupt JSON produces empty store without raising."""
    p = tmp_path / "bad.json"
    p.write_text("{not valid json")
    store = ChatStore(path=p)
    assert store.get("any") is None


# --- Basic CRUD tests ---

def test_set_and_get(tmp_path):
    store = ChatStore(path=tmp_path / "s.json")
    store.set("972546838910", "session-1")
    assert store.get("972546838910") == "session-1"


def test_get_unknown_returns_none(tmp_path):
    store = ChatStore(path=tmp_path / "s.json")
    assert store.get("000000000000") is None


def test_set_persists_to_disk(tmp_path):
    p = tmp_path / "s.json"
    store = ChatStore(path=p)
    store.set("972546838910", "session-1")
    reloaded = ChatStore(path=p)
    assert reloaded.get("972546838910") == "session-1"


# --- Subclass tests ---

def test_claude_session_store_uses_claude_path():
    store = ClaudeSessionStore()
    from src.chat_store import CLAUDE_STORE_PATH
    assert store._path == CLAUDE_STORE_PATH


def test_processed_message_store_deduplication(tmp_path):
    store = ProcessedMessageStore(path=tmp_path / "proc.json")
    store.mark_processed("972546838910", "hello")
    assert store.is_processed("972546838910", "hello")
    assert not store.is_processed("972546838910", "world")


def test_processed_message_store_cleanup(tmp_path):
    """Store trims to 50 entries when it exceeds 100."""
    store = ProcessedMessageStore(path=tmp_path / "proc.json")
    list(map(lambda i: store.mark_processed(str(i), f"msg{i}"), range(101)))
    assert len(store._store) == 50
