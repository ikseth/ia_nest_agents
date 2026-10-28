from __future__ import annotations

from pathlib import Path
import subprocess

import pytest


SCRIPT = Path("deploy/destino/ianest-agente-comando")


def _fake_binaries(directory: Path):
    for name in ("uptime", "free", "systemctl", "journalctl", "df", "ip", "logger"):
        path = directory / name
        path.write_text("#!/bin/sh\nprintf '%s:%s\\n' \"${0##*/}\" \"$*\"\n", encoding="ascii")
        path.chmod(0o755)


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("estado", ("uptime:", "free:-m")),
        ("servicios", ("systemctl:--failed --no-legend --plain --no-pager",)),
        ("journal", ("journalctl:-p err -b --since -24h --no-pager -o short-iso -n 200",)),
        ("disco", ("df:-hPT -x tmpfs -x devtmpfs -x overlay -x squashfs",)),
        ("red", ("ip:-br addr",)),
    ],
)
def test_forced_command_executes_fixed_commands(tmp_path, token, expected):
    _fake_binaries(tmp_path)
    environment = {"PATH": str(tmp_path), "SSH_ORIGINAL_COMMAND": token}
    completed = subprocess.run(["/bin/bash", str(SCRIPT)], env=environment, capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    for item in expected:
        assert item in completed.stdout


@pytest.mark.parametrize("command", ["estado; id", "disco extra", "", "$(id)"])
def test_forced_command_rejects_everything_outside_catalog(tmp_path, command):
    _fake_binaries(tmp_path)
    environment = {"PATH": str(tmp_path), "SSH_ORIGINAL_COMMAND": command}
    completed = subprocess.run(["/bin/bash", str(SCRIPT)], env=environment, capture_output=True, text=True, check=False)
    assert completed.returncode == 2
    assert "fuera de catalogo" in completed.stderr
    assert "id" not in completed.stdout


def test_destination_setup_is_valid_bash():
    completed = subprocess.run(["bash", "-n", "deploy/destino/preparar_destino.sh"], capture_output=True, text=True)
    assert completed.returncode == 0
