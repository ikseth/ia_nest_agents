# ia_nest_agents

Estado: primera entrega en codigo
Version: 0.1.0 - 2026-10-28

`ianest-agents` es la capa exterior que lleva encargos concretos al ente. Esta
primera entrega contiene un gestor y un agente Linux de solo lectura: ejecuta
cinco comprobaciones cerradas por SSH, pide un diagnostico al borde y guarda el
resultado localmente.

El agente no dirige como piensa el ente (`core ADR 0033`). Solo consume la
piel OpenAI de `ia_nest_edge`; el borde aplica la identidad de su cuenta y que
no se escriba memoria. No habla con core ni con extended.

## Instalar

Se requiere Bash, Python >=3.13,<3.14 y PyYAML disponible en ese Python. No se
descargan dependencias: el instalador crea un venv con los paquetes del Python
de despliegue e instala este arbol local.

```bash
deploy/setup.sh /ruta/privada/venv
```

El comando queda en `/ruta/privada/venv/bin/ianest-agents`. No hace falta root
si la ruta es del usuario que ejecutara el agente.

## Configurar y lanzar

Copiar `config/agents.example.yaml` fuera del repo. La configuracion efectiva,
la clave Bearer, la clave SSH y `known_hosts` no se versionan. `known_hosts` es
obligatorio y la verificacion de la clave de host nunca se desactiva.

```bash
/ruta/privada/venv/bin/ianest-agents --config /ruta/privada/agents.yaml linux check host-ejemplo
```

Sin `--config`, la ruta es
`$XDG_CONFIG_HOME/ianest-agents/agents.yaml`, o
`~/.config/ianest-agents/agents.yaml` si no se define `XDG_CONFIG_HOME`.
`--anterior /ruta/informe.json` anade el diagnostico del informe previo a la
pregunta al ente. Solo se admiten hosts declarados en `hosts`.

Cada pasada imprime el informe Markdown y escribe, con la misma marca UTC, un
JSON y un Markdown en `reports_dir/<host>/`. Los ficheros son `600` y los
directorios `700`. La auditoria JSONL no conserva salidas, claves ni
diagnosticos.

## Destino SSH

Como root en cada destino, instalar el comando forzado y el usuario dedicado:

```bash
deploy/destino/preparar_destino.sh ianest_agente /ruta/ianest-agente.pub
```

El comando forzado acepta exclusivamente `estado`, `servicios`, `journal`,
`disco` y `red`. Es el ultimo cerrojo del catalogo que el gestor ya aplica.

Los ejemplos de `deploy/systemd/` llaman al mismo comando una vez al dia; no
incorporan logica de agente.

## Desarrollo

```bash
.venv/bin/python -m pytest -q
```

El plan y las decisiones de alcance viven en `docs/PLAN.md`. Para el orden de
lectura y las normas entre capas, ver `AGENTS.md`.
