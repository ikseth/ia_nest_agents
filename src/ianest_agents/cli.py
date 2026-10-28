"""Interfaz de linea de ordenes de ianest-agents."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .config import ConfigurationError, default_config_path, from_path
from .edge import EdgeError
from .manager import LinuxManager, ManagerError, load_previous_diagnosis


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(prog="ianest-agents")
    command.add_argument("--config", type=Path, default=default_config_path())
    agents = command.add_subparsers(dest="agent", required=True)
    linux = agents.add_parser("linux")
    linux_commands = linux.add_subparsers(dest="linux_command", required=True)
    check = linux_commands.add_parser("check")
    check.add_argument("host")
    check.add_argument("--anterior", type=Path)
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config = from_path(args.config)
        previous = load_previous_diagnosis(args.anterior) if args.anterior else None
        manager = LinuxManager(config)
        result = manager.run(args.host, previous)
    except (ConfigurationError, ManagerError, EdgeError) as exc:
        print(f"ianest-agents: error: {exc}", file=sys.stderr)
        return 2
    print(result["report_markdown"].read_text(encoding="utf-8"), end="")
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
