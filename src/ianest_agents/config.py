"""Carga y validacion de la configuracion privada del agente."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml


class ConfigurationError(ValueError):
    """La configuracion no permite iniciar una pasada."""


@dataclass(frozen=True)
class EdgeSettings:
    base_url: str
    key_file: Path
    ca_file: Path | None
    model: str
    timeout_seconds: float


@dataclass(frozen=True)
class SshSettings:
    user: str
    key_file: Path
    known_hosts_file: Path
    connect_timeout_seconds: int
    command_timeout_seconds: float


@dataclass(frozen=True)
class AgentConfig:
    edge: EdgeSettings
    ssh: SshSettings
    reports_dir: Path
    audit_path: Path
    hosts: dict[str, str]


def default_config_path() -> Path:
    config_home = Path.home() / ".config"
    from os import environ

    if environ.get("XDG_CONFIG_HOME"):
        config_home = Path(environ["XDG_CONFIG_HOME"])
    return config_home / "ianest-agents" / "agents.yaml"


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{name} debe ser un mapa YAML")
    return value


def _keys(values: dict[str, Any], name: str, required: set[str], optional: set[str] = set()) -> None:
    missing = required - values.keys()
    unknown = values.keys() - required - optional
    if missing:
        raise ConfigurationError(f"faltan claves en {name}: {', '.join(sorted(missing))}")
    if unknown:
        raise ConfigurationError(f"claves desconocidas en {name}: {', '.join(sorted(unknown))}")


def _string(values: dict[str, Any], key: str, name: str) -> str:
    value = values[key]
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{name}.{key} debe ser texto no vacio")
    return value


def _positive_number(values: dict[str, Any], key: str, name: str) -> float:
    value = values[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigurationError(f"{name}.{key} debe ser un numero positivo")
    return float(value)


def _positive_integer(values: dict[str, Any], key: str, name: str) -> int:
    value = values[key]
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigurationError(f"{name}.{key} debe ser un entero positivo")
    return value


def from_dict(raw: Any) -> AgentConfig:
    root = _mapping(raw, "raiz")
    _keys(root, "raiz", {"edge", "ssh", "reports_dir", "audit_path", "hosts"})
    edge = _mapping(root["edge"], "edge")
    _keys(edge, "edge", {"base_url", "key_file", "model"}, {"ca_file", "timeout_seconds"})
    ssh = _mapping(root["ssh"], "ssh")
    _keys(
        ssh,
        "ssh",
        {"user", "key_file", "known_hosts_file"},
        {"connect_timeout_seconds", "command_timeout_seconds"},
    )
    hosts_raw = _mapping(root["hosts"], "hosts")
    if not hosts_raw:
        raise ConfigurationError("hosts no puede estar vacio")

    hosts: dict[str, str] = {}
    for host_name, host_value in hosts_raw.items():
        if not isinstance(host_name, str) or not host_name or "/" in host_name or host_name in {".", ".."}:
            raise ConfigurationError("cada nombre de hosts debe ser un nombre de directorio seguro")
        host_map = _mapping(host_value, f"hosts.{host_name}")
        _keys(host_map, f"hosts.{host_name}", {"address"})
        hosts[host_name] = _string(host_map, "address", f"hosts.{host_name}")

    ca_file = edge.get("ca_file")
    if ca_file is not None and (not isinstance(ca_file, str) or not ca_file.strip()):
        raise ConfigurationError("edge.ca_file debe ser texto no vacio si se indica")
    base_url = _string(edge, "base_url", "edge").rstrip("/")
    parsed_url = urlsplit(base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ConfigurationError("edge.base_url debe ser una URL http o https completa")
    return AgentConfig(
        edge=EdgeSettings(
            base_url=base_url,
            key_file=Path(_string(edge, "key_file", "edge")),
            ca_file=Path(ca_file) if ca_file is not None else None,
            model=_string(edge, "model", "edge"),
            timeout_seconds=_positive_number(
                {"timeout_seconds": edge.get("timeout_seconds", 300)}, "timeout_seconds", "edge"
            ),
        ),
        ssh=SshSettings(
            user=_string(ssh, "user", "ssh"),
            key_file=Path(_string(ssh, "key_file", "ssh")),
            known_hosts_file=Path(_string(ssh, "known_hosts_file", "ssh")),
            connect_timeout_seconds=_positive_integer(
                {"connect_timeout_seconds": ssh.get("connect_timeout_seconds", 5)},
                "connect_timeout_seconds",
                "ssh",
            ),
            command_timeout_seconds=_positive_number(
                {"command_timeout_seconds": ssh.get("command_timeout_seconds", 30)},
                "command_timeout_seconds",
                "ssh",
            ),
        ),
        reports_dir=Path(_string(root, "reports_dir", "raiz")),
        audit_path=Path(_string(root, "audit_path", "raiz")),
        hosts=hosts,
    )


def from_path(path: Path) -> AgentConfig:
    try:
        contents = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(f"no se puede leer la configuracion {path}: {exc.strerror}") from exc
    try:
        raw = yaml.safe_load(contents)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"YAML invalido en {path}: {exc}") from exc
    config = from_dict(raw)
    required_files = [
        ("edge.key_file", config.edge.key_file),
        ("ssh.key_file", config.ssh.key_file),
        ("ssh.known_hosts_file", config.ssh.known_hosts_file),
    ]
    if config.edge.ca_file is not None:
        required_files.append(("edge.ca_file", config.edge.ca_file))
    for label, file_path in required_files:
        if not file_path.is_file():
            raise ConfigurationError(f"{label} no es un fichero legible: {file_path}")
        try:
            with file_path.open("rb"):
                pass
        except OSError as exc:
            raise ConfigurationError(f"no se puede leer {label}: {file_path}") from exc
    return config
