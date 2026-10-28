from __future__ import annotations

import subprocess

from ianest_agents.ssh import OpenSshConnector, truncate_output


def test_ssh_command_has_exact_hardening_options(config):
    assert OpenSshConnector.command(config.ssh, "192.0.2.10", "disco") == [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={config.ssh.known_hosts_file}",
        "-o",
        "IdentitiesOnly=yes",
        "-i",
        str(config.ssh.key_file),
        "-o",
        "ConnectTimeout=5",
        "-T",
        "ianest_agente@192.0.2.10",
        "disco",
    ]


def test_connector_sends_only_the_token_as_remote_command(config):
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, b"correcto\n", b"")

    result = OpenSshConnector(runner=runner).check(config.ssh, "192.0.2.10", "red")
    assert calls[0][0][-1] == "red"
    assert calls[0][1]["shell"] is False
    assert result.result == "ok"


def test_truncate_keeps_last_200_lines():
    raw = "".join(f"linea-{number}\n" for number in range(300)).encode()
    output, truncated = truncate_output(raw)
    assert truncated is True
    assert output.splitlines() == [f"linea-{number}" for number in range(100, 300)]


def test_truncate_limits_utf8_output_to_16_kib():
    raw = ("x" * (20 * 1024)).encode()
    output, truncated = truncate_output(raw)
    assert truncated is True
    assert len(output.encode("utf-8")) <= 16 * 1024
    assert output.endswith("x")
