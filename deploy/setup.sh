#!/usr/bin/env bash
# Instala ianest-agents desde este arbol, sin descargar dependencias.

set -Eeuo pipefail

usage() {
  printf 'Uso: %s <ruta_del_venv>\n' "$0" >&2
}

[[ $# -eq 1 ]] || { usage; exit 2; }

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="$1"
python_bin=""
for candidate in python3.13 python3; do
  if command -v "$candidate" >/dev/null 2>&1 &&
    "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 13) or sys.version_info >= (3, 14))'; then
    python_bin="$(command -v "$candidate")"
    break
  fi
done
[[ -n "$python_bin" ]] || { printf '%s\n' 'se requiere Python >=3.13,<3.14' >&2; exit 1; }

if [[ ! -x "$venv_dir/bin/python" ]]; then
  "$python_bin" -m venv --system-site-packages "$venv_dir"
fi
"$venv_dir/bin/python" -c 'import yaml' >/dev/null 2>&1 || {
  printf '%s\n' 'falta PyYAML en el Python de despliegue' >&2
  exit 1
}
"$venv_dir/bin/python" -m pip install --no-deps --no-build-isolation "$repo_dir"
printf 'Instalado: %s/bin/ianest-agents\n' "$venv_dir"
