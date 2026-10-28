"""Cliente minimo de la piel OpenAI del borde."""

from __future__ import annotations

import json
import ssl
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import EdgeSettings


class EdgeError(RuntimeError):
    def __init__(self, message: str, http_status: int | None = None):
        super().__init__(message)
        self.http_status = http_status


class EdgeClient:
    def __init__(self, settings: EdgeSettings, opener=urlopen, monotonic=time.monotonic):
        self._settings = settings
        self._opener = opener
        self._monotonic = monotonic
        self._key = self._read_key(settings.key_file)
        try:
            self._ssl_context = ssl.create_default_context(
                cafile=str(settings.ca_file) if settings.ca_file else None
            )
        except (OSError, ssl.SSLError) as exc:
            raise EdgeError("no se pudo preparar la verificacion TLS del borde") from exc

    @staticmethod
    def _read_key(path: Path) -> str:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise EdgeError(f"no se puede leer edge.key_file {path}: {exc.strerror}") from exc
        if len(lines) != 1 or not lines[0].strip():
            raise EdgeError("edge.key_file debe contener una sola linea no vacia")
        return lines[0].strip()

    @staticmethod
    def prompt(collected: dict, previous_diagnosis: str | None) -> str:
        instruction = (
            "Redacta un diagnostico breve en markdown en castellano: estado general, "
            "problemas por orden de gravedad con la evidencia de la que salen, y que "
            "comprobaria un administrador a continuacion. No inventes lo que no esta "
            "en los datos. Solo lectura: no propongas comandos que cambien el sistema."
        )
        payload: dict[str, object] = {"datos_recogidos": collected}
        if previous_diagnosis is not None:
            payload["diagnostico_anterior"] = previous_diagnosis
        return f"{instruction}\n\nDatos en JSON:\n{json.dumps(payload, ensure_ascii=True, sort_keys=True)}"

    def diagnose(self, collected: dict, previous_diagnosis: str | None = None) -> tuple[str, int, float]:
        body = {
            "model": self._settings.model,
            "stream": False,
            "messages": [{"role": "user", "content": self.prompt(collected, previous_diagnosis)}],
        }
        request = Request(
            f"{self._settings.base_url}/v1/chat/completions",
            data=json.dumps(body, ensure_ascii=True).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = self._monotonic()
        try:
            with self._opener(request, timeout=self._settings.timeout_seconds, context=self._ssl_context) as response:
                status = response.getcode()
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise EdgeError(f"respuesta HTTP {exc.code} del borde", exc.code) from exc
        except (URLError, ssl.SSLError, TimeoutError, OSError) as exc:
            raise EdgeError("no se pudo contactar de forma segura con el borde") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EdgeError("respuesta invalida del borde", status) from exc
        duration = self._monotonic() - started
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise EdgeError("respuesta invalida del borde", status) from exc
        if not isinstance(content, str):
            raise EdgeError("respuesta invalida del borde", status)
        return content, status, duration
