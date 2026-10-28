from __future__ import annotations

from datetime import datetime, timezone
import json
import stat

from ianest_agents.edge import EdgeError
from ianest_agents.manager import LinuxManager
from ianest_agents.ssh import CheckResult


class FakeConnector:
    def __init__(self):
        self.calls = []

    def check(self, settings, address, token):
        self.calls.append((settings, address, token))
        return CheckResult(token, f"salida {token}\n", 0, False, 0.25, 15, "ok")


class FakeEdge:
    def __init__(self, error: EdgeError | None = None):
        self.error = error
        self.calls = []

    def diagnose(self, collected, previous):
        self.calls.append((collected, previous))
        if self.error:
            raise self.error
        return "diagnostico de prueba", 200, 0.5


def _clock():
    return datetime(2026, 10, 28, 12, 34, 56, tzinfo=timezone.utc)


def test_unknown_token_is_audited_without_calling_ssh(config):
    connector = FakeConnector()
    manager = LinuxManager(config, connector=connector, edge_client=FakeEdge(), clock=_clock)
    result = manager.run("host-ejemplo", tokens=("fuera",))

    audit = config.audit_path.read_text(encoding="ascii")
    assert connector.calls == []
    assert result["success"] is False
    assert '"token":"fuera"' in audit
    assert '"result":"rejected"' in audit


def test_edge_failure_still_writes_private_reports_and_never_audits_key(config, tmp_path):
    edge_key = "agent.private-secret"
    (tmp_path / "edge.key").write_text(edge_key + "\n", encoding="utf-8")
    manager = LinuxManager(
        config,
        connector=FakeConnector(),
        edge_client=FakeEdge(EdgeError("respuesta HTTP 503 del borde", 503)),
        clock=_clock,
    )
    result = manager.run("host-ejemplo")

    report = json.loads(result["report_json"].read_text(encoding="utf-8"))
    audit = config.audit_path.read_text(encoding="ascii")
    markdown = result["report_markdown"].read_text(encoding="utf-8")
    assert result["success"] is False
    assert report["edge_error"] == "respuesta HTTP 503 del borde"
    assert len(report["checks"]) == 5
    assert "respuesta HTTP 503" in markdown
    assert edge_key not in audit
    assert edge_key not in result["report_json"].read_text(encoding="utf-8")
    assert '"edge_http_status":503' in audit
    assert '"edge_result":"error"' in audit
    assert stat.S_IMODE(result["report_json"].stat().st_mode) == 0o600
    assert stat.S_IMODE(result["report_markdown"].stat().st_mode) == 0o600
    assert stat.S_IMODE(result["report_json"].parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(config.audit_path.stat().st_mode) == 0o600


def test_previous_diagnosis_reaches_only_the_edge_client(config):
    edge = FakeEdge()
    manager = LinuxManager(config, connector=FakeConnector(), edge_client=edge, clock=_clock)
    manager.run("host-ejemplo", previous_diagnosis="antes")
    assert edge.calls[0][1] == "antes"
    assert "antes" not in config.audit_path.read_text(encoding="ascii")
