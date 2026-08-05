import types


class DummyTool:
    def __init__(self, name="tech_detector"):
        self.name = name

    def execute(self, input_data):
        return types.SimpleNamespace(data={"fresh": True})


class FakeStore:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value


def test_orchestrator_does_not_preserve_previous_session_by_default():
    from agent.orchestrator import Orchestrator

    profile_id = "user-123"
    # Seed the store with stale results that should NOT be kept
    store = FakeStore()
    store.set(profile_id, {"tech_detector": {"stale": True}})

    tools = {"tech_detector": DummyTool()}
    orch = Orchestrator(tools=tools, session_store=store)

    profile_data = {"files": ["src/main.py"]}

    orch.run(profile_id, profile_data)

    # The persisted session for this run should only contain fresh results
    assert profile_id in store.store
    persisted = store.get(profile_id)
    assert "tech_detector" in persisted
    assert persisted["tech_detector"] == {"fresh": True}
