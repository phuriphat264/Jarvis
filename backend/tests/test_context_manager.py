import pytest
from app.core_service.context_manager import ContextManager
from app.core_service.token_counter import SimpleTokenCounter
from app.database.models.message import Message
from app.core.config import settings

def test_token_counter():
    counter = SimpleTokenCounter()
    assert counter.count_text("abc") == 1
    assert counter.count_text("abcdef") == 2
    # test dict messages
    msgs = [{"role": "user", "content": "abc"}]
    # 4 overhead + 1 text + 3 reply prime = 8
    assert counter.count_messages(msgs) == 8

def test_context_manager_budgeting():
    # Setup context manager with small budget
    settings.AI_MAX_TOKENS = 30
    settings.RECENT_MESSAGE_LIMIT = 0 # No limit on count, just token
    cm = ContextManager(SimpleTokenCounter())
    
    # System = 4 + len("sys")/3 (1) = 5
    # New user = 4 + len("new")/3 (1) = 5
    # Base tokens = 5 + 5 + 3 (prime) = 13.
    # Budget left = 30 - 13 = 17 tokens for history.
    
    # Let's create history messages that take 10 tokens each
    # 4 overhead + 6 content tokens (18 chars) = 10 tokens
    msg1 = Message(role="user", content="A" * 18)
    msg2 = Message(role="assistant", content="B" * 18)
    msg3 = Message(role="user", content="C" * 18)
    
    history = [msg1, msg2, msg3] # Oldest to newest
    
    # msg3 (newest) takes 10. Left = 7.
    # msg2 takes 10. Left = -3. (Won't fit)
    # Expected context: system, msg3, new request
    
    messages = cm.build_context("sys", history, "new")
    
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "C" * 18
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "new"

def test_context_manager_ordering():
    settings.AI_MAX_TOKENS = 1000
    cm = ContextManager(SimpleTokenCounter())
    
    msg1 = Message(role="user", content="1")
    msg2 = Message(role="assistant", content="2")
    msg3 = Message(role="user", content="3")
    
    messages = cm.build_context("sys", [msg1, msg2, msg3], "new")
    
    assert len(messages) == 5
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "1"
    assert messages[2]["content"] == "2"
    assert messages[3]["content"] == "3"
    assert messages[4]["content"] == "new"
