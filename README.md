# ia_nest_agents

La capa agentica: agentes que usan el ente IA_NEST para encargos concretos.

Estado: semilla
Version: 0.1 - 2026-10-22

## Que es

Zona **Exterior** del registro (meta ADR 0013, `core ADR 0033`): un agente usa
al ente, le hace encargos y lleva el bucle de cada encargo, pero NO dirige como
piensa el ente.

Se compone de:

- **Un gestor**: registro de agentes, policy y auditoria.
- **Agentes**, por este orden: Linux y Nextcloud, los dos de solo lectura.

Consume el ente a traves de `ia_nest_edge`, con credencial propia por agente.

## Estado

Semilla documental, sin codigo. Va despues de la primera entrega del borde
(meta ADR 0013).

Base previa, a releer contra `core ADR 0033` antes de adoptarla: AGENTS-001 y el
plano Linux de solo lectura del repo `ia_nest` antiguo
(`docs/desarrollo/arquitectura/AGENTS_001_PLANO_AGENTES.md` y
`ADDON_005_LINUX_SSH_READ_ONLY.md`). Son anteriores al ente por capas: su
taxonomia (componentes de core, addons, agentes) no coincide con el registro
actual.

## Orden de lectura

Ver `AGENTS.md`.
