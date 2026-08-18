# alerts

Decide que amerita interrumpir a una persona, y cuando se decide. Lee la base, arma los
eventos, y manda los nuevos por `notify`. No consulta SQL (eso es `store`) ni entrega
mensajes (eso es `notify`).

El cliente ya tenia una bandeja llena de avisos que nadie abria. Por eso una regla entra
solo si perderla cuesta plata o hace repetir trabajo: el recibo que despues del vencimiento
ya no se puede emitir, la factura vencida con saldo, la grande que esta por caer, la orden
que se termina pidiendo dos veces, el reclamo sin responder, y los datos esperando una
confirmacion.

## Como se usa

```python
from alerts import AlertEngine, AlertScheduler

engine = AlertEngine(store, notifier)      # store de `store`, notifier de `notify`
report = engine.run()                       # una pasada, ahora
report.as_dict()                            # {"eventos_nuevos": 3, "entregas": 3, ...}

agenda = AlertScheduler(engine, store)
agenda.start()                              # intervalo + corrida de la manana
agenda.run_now()                            # el boton de "revisar ahora"
agenda.stop()
```

| Parametro | Tipo | Que es |
|---|---|---|
| `store` | `Store` | la base, de la caja `store` |
| `notifier` | `Notifier` | la salida, de la caja `notify` |
| `rules` | lista de `Rule` | por defecto las seis de abajo, en orden de prioridad |
| `texts` | `TextLibrary` | de donde se leen los textos, por defecto `messages/` |
| `engine.run(today)` | str ISO o vacio | la fecha contra la que se mide; sin ella, la de hoy |
| `AlertScheduler(morning_hour)` | int | hora de la corrida diaria, por defecto 8 |
| `AlertScheduler(timezone)` | str o vacio | zona horaria de la corrida diaria, por defecto la del sistema |

## Las reglas

En este orden. El orden importa: si dos reglas hablan de la misma factura en una pasada,
sale la primera y la otra se descarta.

| Regla | Cuando dispara | Severidad | Setting |
|---|---|---|---|
| `recibo_faltante` | factura sin recibo emitido que vence dentro de N dias (todavia no vencida) | urgente | `recibo_dias_antes` |
| `factura_vencida` | factura pasada de vencimiento con saldo mayor a cero | urgente | ninguno |
| `factura_por_vencer` | factura con saldo que vence dentro de N dias y supera el monto minimo | aviso | `aviso_dias_antes`, `aviso_monto_minimo` |
| `orden_vieja` | orden de compra abierta hace mas de N dias (abierta es todo lo que no sea recibida ni anulada) | aviso | `orden_vieja_dias` |
| `reclamo_sin_responder` | mensaje `kind = reclamo` con `resolved = 0` | aviso | ninguno |
| `revision_pendiente` | hay items pendientes en la cola de revision: un solo resumen por dia, no uno por item | aviso | ninguno |

`recibo_faltante` y `factura_vencida` son urgentes porque las dos ya cuestan plata: pasada
la fecha el recibo no se puede emitir, y una factura vencida es la llamada del proveedor.

Los settings se leen de la tabla `setting` en cada pasada, asi que un cambio hecho a las
nueve vale a las diez. Los valores por defecto son los que deja `store` al crear la base.

## Que garantiza

- **Un evento se levanta una sola vez.** La clave de deduplicacion es la regla mas la
  entidad mas su fecha, asi que el mismo vencimiento no se anuncia cada doce horas. Si la
  fecha cambia, es un evento nuevo.
- **Solo se manda lo nuevo.** Un evento que ya existia no se vuelve a enviar.
- **Una entidad, un aviso por pasada.** Una factura sin recibo y encima grande genera un
  solo mensaje: el de la regla de mayor prioridad.
- **Toda entrega queda registrada**, salga o no, en `alert_delivery` con su motivo.
- **Lo que fallo se reintenta.** En cada pasada, antes de evaluar nada, las entregas
  fallidas se mandan de nuevo a los destinatarios que fallaron, sin volver a disparar el
  evento.
- **Una regla rota no calla a las otras cinco.** Su error queda en `errores` del reporte y
  la pasada sigue.
- **Hoy se inyecta.** `run(today="2026-08-18")` mide todo contra esa fecha.

## Los textos

Cada regla tiene su archivo en `messages/<regla>.md`, leido al usar, nunca escrito en el
codigo. La primera linea es el titulo y el resto es el cuerpo; los dos aceptan parametros
con nombre (`{numero}`, `{monto}`, `{vencimiento}`) que completa la regla. Los montos se
escriben con `format_amount` recien en ese momento: adentro siempre son centavos enteros.

El nombre del archivo es tambien el nombre de la plantilla de WhatsApp que hay que aprobar
en Meta, y los parametros del archivo son los parametros de la plantilla. El texto esta
redactado en tono transaccional a proposito: Meta reclasifica como marketing lo que suena
comercial, y lo cobra a esa tarifa.

## Que devuelve una pasada

`AlertRun.as_dict()`:

| Clave | Que cuenta |
|---|---|
| `eventos_nuevos` | eventos levantados por primera vez |
| `eventos_repetidos` | eventos que ya existian, no se mandaron |
| `eventos_salteados` | descartados porque otra regla ya hablo de esa entidad |
| `entregas` | envios aceptados, incluidos los reintentos |
| `entregas_fallidas` | envios rechazados, quedan para el proximo reintento |
| `reintentos` | entregas fallidas que se volvieron a intentar |
| `errores` | reglas que fallaron, en castellano |

## La programacion

Dos disparadores, porque responden a miedos distintos: un intervalo tomado de `sync_horas`
(nunca mas seguido que cada 15 minutos) para que nada espere un dia entero, y una corrida
fija a la manana para que quien abre el negocio ya tenga la lista. Ademas `run_now()`, que
es el boton de la pantalla. Una pasada que explota queda en el log y en `last_error`, y la
programacion sigue en pie.

## Errores

| Error | Cuando |
|---|---|
| `MissingText` | falta el `.md` de una regla, o el texto pide un parametro que la regla no paso |

Que un mensaje no salga no es un error: vuelve como entrega fallida y se reintenta.

## Depende de

`store` (lectura y escritura de eventos y entregas), `notify` (envio), `format_amount` de
`normalizer`, y `apscheduler` para la programacion.
