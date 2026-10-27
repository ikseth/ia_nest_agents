# Instrucciones para agentes de IA en ia_nest_agents

Las reglas transversales del ente (texto ASCII, identificadores en ingles
snake_case, citas `<repo> ADR NNNN`, repo publico, modo ciego, regla del
registro) viven en `ia_nest_meta` y no se repiten aqui. Lee antes:

1. `meta docs/CONVENCIONES_TRANSVERSALES.md` y `meta docs/DOCTRINA_MULTI_IA.md`
2. `meta docs/REGISTRO_CAPAS.md` y `meta docs/ARQUITECTURA_DE_CAPAS.md`
3. `meta ADR 0013` (por que existe este repo) y `meta docs/CAPAS_FUTURAS.md`
   ("quien decide y quien orquesta")
4. `core ADR 0033` y `0034` (el exterior no dirige el pensar del ente)
5. `ia_nest_edge` `README.md` (la puerta por la que se consume el ente)
6. `README.md` de este repo

Orden entre capas: la hoja de ruta del ente, en `meta docs/plan/HOJA_DE_RUTA.md`
(meta ADR 0014). Los hilos de un hito salen de meta; el plan de este repo lleva
solo su detalle interno.

## Reglas propias de este repo

- **El agente lleva el encargo, no el pensar.** El bucle de un encargo es del
  agente; como razona el ente es del core (`core ADR 0033`).
- **Todo pasa por el borde.** Ningun agente habla con extended ni con el core
  directamente.
- **Solo lectura** hasta que se decida otra cosa por ADR. Actuar sobre un
  sistema es de `ia_nest_external_*` (`core ADR 0007`), no de un agente.
- **Credenciales fuera del repo.** Se versiona solo el `.example`.
- Mientras el repo sea semilla, todo documento nuevo nace `Estado: propuesta`.
