from __future__ import annotations

import json

from ianest_agents.edge import EdgeClient
import ianest_agents.edge as edge_module


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False

    def getcode(self):
        return 200

    def read(self):
        return json.dumps(self.payload).encode()


def test_openai_request_is_single_user_message_and_uses_ca(config, tmp_path, monkeypatch):
    key = tmp_path / "edge.key"
    key.write_text("agent.secret-value\n", encoding="utf-8")
    contexts = []
    calls = []

    def create_default_context(*, cafile=None):
        contexts.append(cafile)
        return "ssl-context"

    def opener(request, *, timeout, context):
        calls.append((request, timeout, context))
        return Response({"choices": [{"message": {"content": "diagnostico"}}]})

    monkeypatch.setattr(edge_module.ssl, "create_default_context", create_default_context)
    client = EdgeClient(config.edge, opener=opener)
    diagnostic, status, _duration = client.diagnose({"checks": []})

    request, timeout, context = calls[0]
    body = json.loads(request.data.decode())
    assert request.full_url == "https://edge.example.test/v1/chat/completions"
    assert request.get_header("Authorization") == "Bearer agent.secret-value"
    assert timeout == 300
    assert context == "ssl-context"
    assert contexts == [str(config.edge.ca_file)]
    assert body["model"] == "diagnostico"
    assert body["stream"] is False
    assert body["messages"] and len(body["messages"]) == 1
    assert body["messages"][0]["role"] == "user"
    assert "system" not in body
    assert "tools" not in body
    assert diagnostic == "diagnostico"
    assert status == 200
