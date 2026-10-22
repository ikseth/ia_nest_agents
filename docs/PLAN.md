# Plan de ia_nest_agents

Estado: propuesta
Version: 0.1 - 2026-10-22

## Primera entrega: el gestor y el agente Linux de solo lectura

Va despues de la primera entrega de `ia_nest_edge` (meta ADR 0013). Se disena
antes, para que el brief este listo cuando el borde pase su visita de
laboratorio.

Lo que ya esta fijado:

- El agente consume el ente por la piel OpenAI del borde, como un consumidor
  mas: su clave, su identidad y su menu. No necesita la segunda entrega del
  borde ni ningun CR al core o a extended.
- El bucle del encargo es del agente; varias llamadas sencillas, no `task.run`.
  El obstaculo de la Fase 7b de extended no le afecta.
- Leer el sistema es del agente, no del ente. Del ADDON-005 del `ia_nest`
  antiguo se reaprovechan las salvaguardas (`BatchMode`, `known_hosts`
  fijado, solo clave publica, usuario dedicado y restringido en destino,
  `systemd-journal` para logs, lista blanca en fail2ban, catalogo cerrado), no
  su ubicacion en el core ni sus mutaciones.
- **Solo lectura impuesta en el destino** (usuario sin `sudo`), no confiada al
  modelo.
- Inventario de hosts y claves fuera del repo.

## Decisiones antes del brief

Con el usuario, una a una:

1. **Forma del agente. DECIDIDA el 2026-10-22: comprobaciones fijas e
   informe.** Una pasada: el agente ejecuta un conjunto cerrado del catalogo
   (estado, servicios caidos, errores recientes del journal, disco, red),
   recorta la salida y pide al ente un diagnostico. El bucle guiado por el ente
   (propone la siguiente comprobacion dentro del catalogo) queda para la
   segunda entrega, sobre el conector, catalogo, policy y auditoria de esta.
2. **Como se invoca. DECIDIDA el 2026-10-22: a mano, con temporizador
   opcional.** La pieza base es un comando (`<agente> linux check <host>`). Un
   temporizador de systemd que llama a ese mismo comando va como ejemplo
   (`.example`), sin logica propia; lo activa el operador. Invocarlo desde una
   conversacion queda aparcado: exigiria que el ente llame a un agente
   (`tools`, que el borde rechaza) e invertiria la direccion. Disparador: cuando
   exista una forma de que el ente encargue trabajo sin dirigirlo
   (`meta docs/CAPAS_FUTURAS.md`, "quien decide y quien orquesta").
3. **Memoria. DECIDIDA el 2026-10-22: informes efimeros.** Lo que el agente
   ve no entra en la memoria del ente; la memoria queda limpia para estudiar el
   uso de la familia. El historico lo guarda el agente en sus informes
   (decision 5) y, si hace falta comparar, el agente pasa el resumen anterior
   en la pregunta. Requiere en el borde una opcion por consumidor que envie
   `write_back=false` (anexo a edge ADR 0002 y ronda corta de Codex, antes del
   agente).
4. **Donde corre** y con que credenciales.
5. **Donde deja el informe**.

## Aparcado

- Mutaciones (reiniciar servicios, runbooks): son de `ia_nest_external_*`.
- Agente Nextcloud: despues del Linux.
