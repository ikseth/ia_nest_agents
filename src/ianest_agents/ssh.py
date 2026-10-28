"""Conector del catalogo Linux por el cliente OpenSSH del sistema."""

from __future__ import annotations

from dataclasses import dataclass
import subprocess
import time

from .config import SshSettings


@dataclass(frozen=True)
class CheckResult:
    token: str
    output: str
    exit_code: int
    truncated: bool
    duration_seconds: float
    bytes_received: int
    result: str


def truncate_output(raw: bytes, max_lines: int = 200, max_bytes: int = 16 * 1024) -> tuple[str, bool]:
    """Conserva el final UTF-8 de una salida, dentro de ambos limites."""
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    selected = "".join(lines[-max_lines:]) if len(lines) > max_lines else text
    truncated = len(lines) > max_lines
    encoded = selected.encode("utf-8")
    if len(encoded) <= max_bytes:
        return selected, truncated

    truncated = True
    low, high = 0, len(selected)
    while low < high:
        middle = (low + high) // 2
        if len(selected[middle:].encode("utf-8")) <= max_bytes:
            high = middle
        else:
            low = middle + 1
    return selected[low:], truncated


class OpenSshConnector:
    """Ejecuta exactamente un token catalogado como comando remoto."""

    def __init__(self, runner=subprocess.run, monotonic=time.monotonic):
        self._runner = runner
        self._monotonic = monotonic

    @staticmethod
    def command(settings: SshSettings, address: str, token: str) -> list[str]:
        return [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={settings.known_hosts_file}",
            "-o",
            "IdentitiesOnly=yes",
            "-i",
            str(settings.key_file),
            "-o",
            f"ConnectTimeout={settings.connect_timeout_seconds}",
            "-T",
            f"{settings.user}@{address}",
            token,
        ]

    def check(self, settings: SshSettings, address: str, token: str) -> CheckResult:
        command = self.command(settings, address, token)
        started = self._monotonic()
        try:
            completed = self._runner(
                command,
                shell=False,
                capture_output=True,
                timeout=settings.command_timeout_seconds,
                check=False,
            )
            raw = (completed.stdout or b"") + (completed.stderr or b"")
            exit_code = completed.returncode
            result = "ok" if exit_code == 0 else "failed"
        except subprocess.TimeoutExpired as exc:
            raw = (exc.stdout or b"") + (exc.stderr or b"")
            exit_code = 124
            result = "timeout"
        except OSError:
            raw = b""
            exit_code = 127
            result = "failed"
        duration = self._monotonic() - started
        output, truncated = truncate_output(raw)
        return CheckResult(
            token=token,
            output=output,
            exit_code=exit_code,
            truncated=truncated,
            duration_seconds=duration,
            bytes_received=len(raw),
            result=result,
        )
