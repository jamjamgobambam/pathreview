import pytest
from unittest.mock import MagicMock
from agent.orchestrator import Orchestrator

class MockSessionStore:
    def __init__(self):
        self.store = {}
        self.set_calls = 0

    def get(self, session_id):
        return self.store.get(session_id)

    def set(self, session_id, data, ttl_seconds=3600):
        self.set_calls += 1
        self.store[session_id] = data.copy()

class SuccessTool:
    name = "tech_detector"
    def execute(self, input_data):
        return {"detected": ["python"]}

class CrashingTool:
    name = "readme_scorer"
    def execute(self, input_data):
        # Raise KeyboardInterrupt to simulate a server crash, 
        # bypassing the generic `except Exception` block.
        raise KeyboardInterrupt("Server crash")

def test_orchestrator_loses_state_on_crash():
    """
    Reproduces the issue where long-running reviews lose progress
    if a server restarts (simulated by a crash). The state is only
    persisted at the end of the run, not incrementally.
    """
    session_store = MockSessionStore()
    tools = {
        "tech_detector": SuccessTool(),
        "readme_scorer": CrashingTool()
    }
    
    orchestrator = Orchestrator(tools=tools, session_store=session_store)
    
    profile_data = {
        "files": ["main.py"],
        "readme_content": "hello world"
    }
    
    with pytest.raises(KeyboardInterrupt):
        orchestrator.run("profile_1", profile_data)
        
    # The tech_detector tool succeeded before the crash.
    # We expect its progress to be saved in the session store.
    
    assert "profile_1" in session_store.store
    assert "tech_detector" in session_store.store["profile_1"]
    assert session_store.set_calls == 1

def test_orchestrator_should_persist_incrementally():
    """
    This is the failing test that defines the expected behavior:
    The orchestrator should save state incrementally after each tool.
    """
    session_store = MagicMock()
    tools = {
        "tech_detector": SuccessTool(),
        "readme_scorer": SuccessTool()
    }
    
    orchestrator = Orchestrator(tools=tools, session_store=session_store)
    profile_data = {
        "files": ["main.py"],
        "readme_content": "hello world"
    }
    
    orchestrator.run("profile_1", profile_data)
    
    # We have 2 tools in the plan, so it should persist state at least twice.
    # Currently this will fail because it only persists once at the end!
    assert session_store.set.call_count >= 2, "State should be persisted incrementally"
