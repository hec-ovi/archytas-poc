# notify

Entrega mensajes. Recibe un texto y un destinatario, y lo saca por el canal que este
configurado: WhatsApp, Telegram o la bandeja local.

No sabe nada de facturas, vencimientos ni reglas de negocio. Quien llama ya decidio que
decir; esta caja solo se ocupa de que llegue y de contar si llego.

## La regla de oro

Un envio que falla no rompe nada. Cada intento vuelve como un `Delivery` que dice si se
entrego, con que id del proveedor, y por que no cuando no. El que llama guarda el
resultado y reintenta despues. La caja solo levanta una excepcion si la configuracion
esta mal escrita.

## Que ofrece

### `Message(text, template=None)` y `Template(name, language, params)`
| Campo | Tipo | Que es |
|---|---|---|
| `text` | str | el aviso en palabras, lo que entrega cualquier canal |
| `template` | `Template` o `None` | solo lo usa WhatsApp, para llegar con la ventana de 24h cerrada |
| `Template.name` | str | nombre de la plantilla aprobada por Meta |
| `Template.language` | str | codigo de idioma, por defecto `es_AR` |
| `Template.params` | dict | parametros con nombre (`{"due_date": "21/08/2026"}`) |

Los dos viajan juntos: el mismo aviso sale como plantilla por WhatsApp y como texto por
Telegram o la bandeja.

### `Notifier`
| Metodo | Que hace |
|---|---|
| `Notifier.from_env(env=None)` | arma los canales leyendo el entorno |
| `Notifier.from_config(config, client=None)` | igual, con un `NotifyConfig` ya armado |
| `Notifier(channels)` | con los canales ya construidos |
| `send(message, recipients=None) -> list[Delivery]` | un `Delivery` por canal y destinatario; sin `recipients` usa los del entorno |
| `channels -> tuple[str, ...]` | los canales que quedaron activos |
| `close()` | cierra los clientes HTTP |

### `Delivery`
| Campo | Tipo | Que es |
|---|---|---|
| `channel` | str | `whatsapp`, `telegram` o `outbox` |
| `recipient` | str | a quien se le mando |
| `delivered` | bool | si el proveedor lo acepto |
| `message_id` | str o `None` | el id del proveedor (`wamid...` en WhatsApp) |
| `reason` | str o `None` | por que no salio, en castellano |
| `as_dict()` | dict | para guardar o mandar por HTTP |

### Canales
| Canal | Que hace | Necesita |
|---|---|---|
| `WhatsAppChannel` | `POST graph.facebook.com/v25.0/<PHONE_ID>/messages`. Manda plantilla, o texto libre si el `Message` no trae plantilla. | token, id de numero, destinatarios |
| `TelegramChannel` | `POST api.telegram.org/bot<TOKEN>/sendMessage`. Solo texto. | token del bot, chat ids |
| `OutboxChannel` | escribe una linea JSON por mensaje y la guarda tambien en memoria (`entries`) | nada |

Un canal propio se agrega implementando `Channel`: `send(recipient, message) -> Delivery`.

## Errores

| Error | Cuando |
|---|---|
| `UnknownChannel` | `NOTIFY_CHANNELS` nombra un canal que no existe |

Que un mensaje no salga no es un error: vuelve como `Delivery` con `delivered=False` y su
`reason`. Los codigos de Meta que se traducen a castellano: `131030` (el numero no esta en
la lista de permitidos), `131047` (pasaron mas de 24h, hace falta plantilla), `131026` (no
se pudo entregar), `190` (token vencido), `132000` y `132001` (plantilla mal usada o
inexistente). Cualquier otro viaja con su codigo y el detalle de Meta. Telegram no tiene
mapeo: su cuerpo de error se relaya tal cual, porque no esta documentado en la
investigacion que sostiene esta caja.

## Invariantes

- Ningun envio fallido levanta una excepcion.
- Sin credenciales el aviso igual queda registrado: la bandeja local siempre esta.
- Un `send` devuelve exactamente un `Delivery` por canal y destinatario.
- Los numeros se guardan como los reporta WhatsApp, con el 9 (`5491122334455`), y el 9 se
  saca recien al mandar, en modo desarrollo.
- Un `200` de Meta significa aceptado, no entregado. La entrega real llega por webhook,
  que esta caja no implementa.

## Como se configura

Variables de entorno:

| Variable | Que es | Por defecto |
|---|---|---|
| `NOTIFY_CHANNELS` | canales separados por coma (`whatsapp,outbox`) | los que tengan credenciales, si no `outbox` |
| `WHATSAPP_TOKEN` | token de acceso de Meta | vacio |
| `WHATSAPP_PHONE_ID` | id del numero (numerico, no el telefono) | vacio |
| `WHATSAPP_RECIPIENTS` | telefonos separados por coma, formato internacional | vacio |
| `WHATSAPP_MODE` | `development` o `production` | `development` |
| `WHATSAPP_API_VERSION` | version de la Graph API | `v25.0` |
| `TELEGRAM_TOKEN` | token del bot de @BotFather | vacio |
| `TELEGRAM_CHAT_IDS` | chat ids separados por coma | vacio |
| `NOTIFY_OUTBOX_PATH` | archivo de la bandeja local | `<CORDILLERA_DATA_DIR o "data">/inbox/outbox.jsonl` |

Si a un canal le faltan credenciales, se cae solo y el aviso va a la bandeja. Nada se
rompe por una variable vacia.

### Que tiene que conseguir el cliente para que WhatsApp funcione

1. **Una linea de telefono dedicada** para el sistema, borrada antes de WhatsApp comun y
   de WhatsApp Business: un numero registrado en la Cloud API no puede estar activo en
   esas apps.
2. **Una cuenta de Meta Business** con la app de WhatsApp creada. De ahi salen el
   `WHATSAPP_PHONE_ID` y el token. Conviene un token de usuario de sistema, que no vence;
   el token temporal del panel dura 24 horas.
3. **Una plantilla de utilidad aprobada** en `es_AR`, con parametros con nombre, redactada
   en tono estrictamente transaccional. Si Meta la juzga promocional la aprueba como
   marketing y la cobra a tarifa de marketing.
4. **Consentimiento por numero**: cada persona que reciba avisos tiene que dar permiso por
   escrito, y ese permiso se guarda con fecha. Lo pide la politica de WhatsApp y no hace
   excepcion con los empleados.
5. **Modo desarrollo**: con el numero de prueba de Meta solo se puede escribir a hasta 5
   telefonos cargados a mano en el panel, y hay que dejar `WHATSAPP_MODE=development` para
   que se saque el 9 de los celulares argentinos.

### Costos

Meta cobra por mensaje de plantilla entregado, segun categoria y pais. Los avisos de
vencimiento son categoria utilidad, la mas barata. Con unos pocos empleados y unos pocos
avisos por dia el gasto es de centavos por mes.

Desde el **2026-10-01** cambia una parte: las respuestas de texto libre dentro de la
ventana de 24 horas pasan a cobrarse, y las plantillas de utilidad dejan de ser gratis
dentro de esa ventana. Las dos se cobran a la tarifa de utilidad del pais, sin descuentos
por volumen. Meta publica las tarifas exactas antes del 2026-09-01. Por eso el sistema se
apoya en plantillas, que tienen costo previsible, y no en la ventana gratuita.

## Depende de

`httpx`. Nada del resto del proyecto.
