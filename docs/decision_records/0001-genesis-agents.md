# Decision 0001: genesis de la capa agentica

Fecha: 2026-10-22

## Decision

Se siembra `ia_nest_agents` como semilla documental, sin codigo ni contrato
publico. Su forma (gestor y agentes de solo lectura), su zona (Exterior) y su
orden (despues del borde) estan decididos en meta ADR 0013; este repo no los
repite.

## Motivo

El repo figuraba como previsto en `meta docs/REGISTRO_CAPAS.md`. El usuario lo
crea junto al borde para que la capa agentica nazca organizada, con su gestor,
en vez de como agentes sueltos.

## Consecuencia

- La fila de la capa en `meta docs/REGISTRO_CAPAS.md` pasa a semilla.
- El diseno del gestor y del agente Linux se abre cuando el borde haya hecho su
  primera entrega. Hasta entonces no hay consumidor que lo ejerza
  (`core ADR 0035`).
- Sin SemVer ni tag hasta que exista contrato publico.

## Impacto de version

Ninguno: no hay contrato publico.
