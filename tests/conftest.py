from __future__ import annotations

from pathlib import Path

import pytest

from ianest_agents.config import AgentConfig, from_dict


@pytest.fixture
def config(tmp_path: Path) -> AgentConfig:
    return from_dict(
        {
            "edge": {
                "base_url": "https://edge.example.test",
                "key_file": str(tmp_path / "edge.key"),
                "ca_file": str(tmp_path / "edge-ca.pem"),
                "model": "diagnostico",
            },
            "ssh": {
                "user": "ianest_agente",
                "key_file": str(tmp_path / "ssh.key"),
                "known_hosts_file": str(tmp_path / "known_hosts"),
            },
            "reports_dir": str(tmp_path / "reports"),
            "audit_path": str(tmp_path / "audit" / "audit.jsonl"),
            "hosts": {"host-ejemplo": {"address": "192.0.2.10"}},
        }
    )
