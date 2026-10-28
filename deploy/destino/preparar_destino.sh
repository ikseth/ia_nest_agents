#!/usr/bin/env bash
# Prepara el usuario remoto de solo lectura para ianest-agents.

set -Eeuo pipefail

usage() {
  printf 'Uso: %s <usuario> <fichero_de_clave_publica>\n' "$0" >&2
}

error() {
  printf 'preparar_destino.sh: %s\n' "$*" >&2
  exit 1
}

[[ $# -eq 2 ]] || { usage; exit 2; }
[[ $(id -u) -eq 0 ]] || error "debe ejecutarse como root"

user="$1"
public_key_file="$2"
[[ "$user" =~ ^[a-z_][a-z0-9_-]*$ ]] || error "usuario invalido"
[[ -r "$public_key_file" ]] || error "no se puede leer la clave publica"
mapfile -t public_key_lines < "$public_key_file"
[[ ${#public_key_lines[@]} -eq 1 && -n ${public_key_lines[0]} ]] ||
  error "la clave publica debe contener una sola linea no vacia"
getent group systemd-journal >/dev/null || error "no existe el grupo systemd-journal"

if ! id "$user" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash --password '!' "$user"
fi
usermod --append --groups systemd-journal "$user"

install -d -m 755 /usr/local/libexec
install -m 755 "$(dirname "$0")/ianest-agente-comando" /usr/local/libexec/ianest-agente-comando

home_directory="$(getent passwd "$user" | cut -d: -f6)"
[[ -n "$home_directory" ]] || error "no se pudo resolver el hogar del usuario"
install -d -o "$user" -g "$(id -gn "$user")" -m 700 "$home_directory/.ssh"
authorized_keys="$home_directory/.ssh/authorized_keys"
forced_line="restrict,command=\"/usr/local/libexec/ianest-agente-comando\" ${public_key_lines[0]}"
printf '%s\n' "$forced_line" > "$authorized_keys"
chown "$user:$(id -gn "$user")" "$authorized_keys"
chmod 600 "$authorized_keys"
