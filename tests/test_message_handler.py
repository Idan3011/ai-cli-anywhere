"""TDD: Message handler tests written FIRST"""

import pytest
from src.message_handler import MessageHandler, ChatMessage, MessageAction


def test_message_immutable():
    """Test that ChatMessage is frozen"""
    msg = ChatMessage(sender="+1234567890", content="test", timestamp=123)
    
    with pytest.raises(Exception):
        msg.sender = "+9999999999"


def test_action_immutable():
    """Test that MessageAction is frozen"""
    action = MessageAction(should_respond=True)
    
    with pytest.raises(Exception):
        action.should_respond = False


def test_should_process_allowed_number():
    """Test processing allowed number"""
    handler = MessageHandler(allowed_phone="+1234567890")
    msg = ChatMessage(sender="+1234567890", content="hello", timestamp=123)
    
    action = handler.should_process(msg)
    
    assert action.should_respond is True
    assert action.reason is None


def test_should_process_blocked_number():
    """Test blocking unauthorized number"""
    handler = MessageHandler(allowed_phone="+1234567890")
    msg = ChatMessage(sender="+9999999999", content="hello", timestamp=123)
    
    action = handler.should_process(msg)
    
    assert action.should_respond is False
    assert "Unauthorized" in action.reason


def test_filter_messages_iterator():
    """Test filtering messages using iterator (NO for loops)"""
    handler = MessageHandler(allowed_phone="+1234567890")
    messages = [
        ChatMessage(sender="+1234567890", content="allowed", timestamp=1),
        ChatMessage(sender="+9999999999", content="blocked", timestamp=2),
        ChatMessage(sender="+1234567890", content="allowed2", timestamp=3),
    ]
    
    filtered = handler.filter_messages(messages)
    
    assert len(filtered) == 2
    assert all(msg.sender == "+1234567890" for msg in filtered)
