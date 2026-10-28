"""Registro, politica, auditoria e informe del agente Linux."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import monotonic
from typing import Callable, Iterable

from .config import AgentConfig
from .edge import EdgeClient, EdgeError
from .ssh import CheckResult, OpenSshConnector


LINUX_CATALOG = ("estado", "servicios", "journal", "disco", "red")


class ManagerError(RuntimeError):
    """La pasada no se puede iniciar con la politica actual."""


def _private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path, 0o700)


class AuditLogger:
    def __init__(self, path: Path):
        self.path = path

    def write(self, event: dict) -> None:
        _private_directory(self.path.parent)
        with self.path.open("a", encoding="ascii") as handle:
            os.chmod(self.path, 0o600)
            handle.write(json.dumps(event, ensure_ascii=True, separators=(",", ":")) + "\n")


class LinuxManager:
    """Gestiona el unico agente registrado en esta primera entrega."""

    agents = {"linux": LINUX_CATALOG}

    def __init__(
        self,
        config: AgentConfig,
        connector: OpenSshConnector | None = None,
        edge_client: EdgeClient | None = None,
        audit_logger: AuditLogger | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self.config = config
        self.connector = connector or OpenSshConnector()
        self.edge_client = edge_client or EdgeClient(config.edge)
        self.audit = audit_logger or AuditLogger(config.audit_path)
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def _check_dict(check: CheckResult) -> dict:
        return asdict(check)

    def _audit_check(self, host: str, check: CheckResult) -> None:
        self.audit.write(
            {
                "type": "check",
                "agent": "linux",
                "host": host,
                "token": check.token,
                "exit_code": check.exit_code,
                "bytes_received": check.bytes_received,
                "truncated": check.truncated,
                "duration_seconds": check.duration_seconds,
                "result": check.result,
            }
        )

    def _rejected(self, host: str, token: str) -> CheckResult:
        check = CheckResult(token, "", 2, False, 0.0, 0, "rejected")
        self._audit_check(host, check)
        return check

    def run(self, host: str, previous_diagnosis: str | None = None, tokens: Iterable[str] = LINUX_CATALOG) -> dict:
        if host not in self.config.hosts:
            raise ManagerError(f"host no configurado: {host}")
        checks: list[CheckResult] = []
        for token in tokens:
            if token not in LINUX_CATALOG:
                checks.append(self._rejected(host, token))
                continue
            check = self.connector.check(self.config.ssh, self.config.hosts[host], token)
            self._audit_check(host, check)
            checks.append(check)

        now = self.clock().astimezone(timezone.utc)
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        data: dict = {
            "agent": "linux",
            "host": host,
            "address": self.config.hosts[host],
            "timestamp_utc": now.isoformat().replace("+00:00", "Z"),
            "checks": [self._check_dict(check) for check in checks],
            "diagnostic": None,
            "edge_error": None,
        }
        edge_status: int | None = None
        edge_duration: float | None = None
        edge_started = monotonic()
        try:
            diagnostic, edge_status, edge_duration = self.edge_client.diagnose(data, previous_diagnosis)
            data["diagnostic"] = diagnostic
        except EdgeError as exc:
            edge_status = exc.http_status
            edge_duration = monotonic() - edge_started
            data["edge_error"] = str(exc)

        report_json, report_markdown = self._write_reports(host, stamp, data)
        checks_ok = all(check.result == "ok" for check in checks)
        edge_ok = data["edge_error"] is None
        outcome = "ok" if checks_ok and edge_ok else "error"
        self.audit.write(
            {
                "type": "pass",
                "agent": "linux",
                "host": host,
                "result": outcome,
                "edge_result": "ok" if edge_ok else "error",
                "edge_http_status": edge_status,
                "edge_duration_seconds": edge_duration,
                "report_json_path": str(report_json),
                "report_markdown_path": str(report_markdown),
            }
        )
        return {
            "success": outcome == "ok",
            "data": data,
            "report_json": report_json,
            "report_markdown": report_markdown,
        }

    def _write_reports(self, host: str, stamp: str, data: dict) -> tuple[Path, Path]:
        directory = self.config.reports_dir / host
        _private_directory(directory)
        json_path = directory / f"{stamp}.json"
        markdown_path = directory / f"{stamp}.md"
        self._write_private(json_path, json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True) + "\n")
        self._write_private(markdown_path, self._markdown(data))
        return json_path, markdown_path

    @staticmethod
    def _write_private(path: Path, contents: str) -> None:
        temporary = path.with_name(f".{path.name}.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(contents)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)

    @staticmethod
    def _markdown(data: dict) -> str:
        lines = [f"# Informe Linux: {data['host']}", "", f"Fecha UTC: {data['timestamp_utc']}", ""]
        if data["diagnostic"] is not None:
            lines.extend(["## Diagnostico", "", data["diagnostic"], ""])
        else:
            lines.extend(["## Error del borde", "", data["edge_error"], ""])
        lines.extend(["## Datos recogidos", ""])
        for check in data["checks"]:
            lines.extend(
                [
                    f"### {check['token']}",
                    "",
                    f"Codigo de salida: {check['exit_code']}",
                    f"Recibidos: {check['bytes_received']} bytes",
                    f"Recortado: {'si' if check['truncated'] else 'no'}",
                    f"Duracion: {check['duration_seconds']:.3f} segundos",
                    "",
                    "```text",
                    check["output"],
                    "```",
                    "",
                ]
            )
        return "\n".join(lines)


def load_previous_diagnosis(path: Path) -> str:
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManagerError(f"no se puede leer el informe anterior {path}") from exc
    diagnostic = previous.get("diagnostic") if isinstance(previous, dict) else None
    if not isinstance(diagnostic, str) or not diagnostic:
        raise ManagerError(f"el informe anterior no contiene un diagnostico: {path}")
    return diagnostic
