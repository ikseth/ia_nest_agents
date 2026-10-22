# Plan de ia_nest_agents

Estado: propuesta
Version: 0.3 - 2026-10-22 (las cinco decisiones cerradas)

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
  `systemd-journal` para logs, catalogo cerrado), no su ubicacion en el core
  ni sus mutaciones. Si un destino ya tuviera fail2ban, podria banear al
  agente por abrir muchas conexiones SSH: nota de diagnostico, no requisito.
- **Contencion en capas**, ninguna confiada al modelo:
  1. **El sistema operativo.** El agente se instala en su entorno como un
     usuario normal; en cada destino entra por SSH con otro usuario normal.
     Ninguno es root ni puede escalar salvo que se le incorpore a sudo. Es la
     contencion que el sistema da sin hacer nada.
  2. **El filtro.** El gestor aplica la policy (catalogo de comandos
     permitidos) y la audita; el comando forzado de `authorized_keys` en el
     destino repite el catalogo como ultimo cerrojo, valido aunque el agente
     estuviera comprometido.
  3. **Conscience (futuro).** Supervisa el pensar del ente, no los actos del
     agente: encaja en la segunda entrega, cuando el ente PROPONGA la
     siguiente comprobacion y conscience pueda vetar esa propuesta.
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
4. **Donde corre. DECIDIDO el 2026-10-22: fuera de la infraestructura del
   ente.** El agente vive en un entorno propio y especifico (maquina o VM
   aparte), no en ninguna maquina de IA_NEST. Asi queda aislado y contenido:
   si hay que cortarlo, se corta su entorno sin tocar el ente. Consecuencias:
   - habla con el borde por la red de casa, como cualquier otro consumidor;
   - su clave del borde viaja por la red: TLS esta disponible en el borde
     (edge ADR 0002, punto 8) y se decide en el laboratorio si se activa;
   - sistema del entorno: openSUSE Tumbleweed; Debian como alternativa.
   Credenciales: su clave del borde y su clave SSH, fuera del repo, en su
   entorno. Destino: usuario normal y comando forzado (contencion, arriba).
   Las credenciales podran salir de un LDAP si se monta (en estudio, tarjeta
   en Deck).
5. **Donde deja el informe. DECIDIDA el 2026-10-22: pantalla y fichero en su
   entorno.** El informe de cada ejecucion son los datos recogidos (recortados,
   JSON) mas el diagnostico del ente (markdown). Lanzado a mano, sale por la
   salida estandar; siempre, ademas, un fichero por host y ejecucion, con
   fecha, en el entorno del agente: es el historico de la decision 3. Sacarlo
   de su entorno (Nextcloud, Deck, notificaciones) seria escribir en otro
   sistema: aparcado hasta el agente Nextcloud, que tendra esas credenciales.

## Aparcado

- Mutaciones (reiniciar servicios, runbooks): son de `ia_nest_external_*`.
- **Aprobador**: interactuar con el agente para aprobarle comandos concretos.
  Segunda entrega o posterior. Al disenarlo: lo aprobado no puede saltarse el
  comando forzado del destino, asi que el aprobador elige dentro de una lista
  ampliada declarada en el destino, no comandos libres.
- Agente Nextcloud: despues del Linux.
