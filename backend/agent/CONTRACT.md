# agent

El modelo con herramientas. Entra una pregunta o una orden en castellano, sale una respuesta
y el rastro de que herramientas corrio y con que argumentos.

Todo lo que una regla puede decidir ya lo decidio una regla. Esta caja entra donde hace falta
criterio: leer una factura que el proveedor mando como foto, entender que "cuanto le debemos
a Cuyo" es una consulta de cuenta, y convertir "registra 200 mil en la F-7797" en un pago.

## La regla de oro

El modelo no calcula, no interpreta y no inventa. Cada numero sale de una herramienta que lo
leyo de la base, cada fecha la interpreta `normalizer`, cada archivo lo lee `document_parser`
y cada proveedor lo resuelve el catalogo de `ingest`. Si una herramienta no lo dio, no existe.

## Como se usa

```python
from agent import Agent

respuesta = Agent(store).ask("cuanto le debemos a Herramientas Cuyo?", user="marcela")
respuesta.text                  # "Le debemos $4.097.341,00 a Herramientas Cuyo SRL."
respuesta.as_dict()["pasos"]    # que herramienta corrio, con que argumentos y que devolvio
```

| Parametro | Tipo | Que es |
|---|---|---|
| `store` | `Store` | la base, de la caja `store` |
| `settings` | `AgentSettings` | donde vive el modelo. Sin esto, sale del entorno |
| `question` | str | lo que escribio la persona |
| `user` | str | quien pregunta. Sin esto ninguna herramienta que escribe corre |

## Que ofrece

### `Agent(store, settings=None)`
| Metodo | Que hace |
|---|---|
| `ask(question, user="") -> Answer` | contesta, corriendo las herramientas que hagan falta |
| `tools -> tuple[str, ...]` | los nombres de las herramientas disponibles |
| `close()` | cierra el cliente HTTP |

### `Answer`
| Campo | Tipo | Que es |
|---|---|---|
| `text` | str | la respuesta en palabras |
| `steps` | tuple[`ToolStep`] | una entrada por herramienta que corrio |
| `turns` | int | cuantas vueltas al modelo hicieron falta |
| `complete` | bool | `False` si corto por el limite de vueltas |
| `tools_used` | tuple[str, ...] | los nombres, en orden |
| `as_dict()` | dict | `respuesta`, `pasos`, `vueltas`, `completo` |

### `ToolStep`
`tool` (que corrio), `arguments` (con que), `result` (que devolvio), `failed` (si volvio con
error), `as_dict()`.

### `ToolRegistry(store)` y `ChatClient(settings)`
El registro arma las herramientas, expone sus esquemas JSON (`schemas`) y despacha una por
nombre (`dispatch(name, arguments, user)`). El cliente habla con cualquier endpoint
compatible con OpenAI y maneja la vuelta de herramientas.

## Las herramientas

Los montos entran y salen en centavos enteros, y ademas vuelven escritos (`"$200.000,00"`).
Las fechas salen en ISO `AAAA-MM-DD`; las que entran se interpretan con `normalizer`, en el
formato que vengan.

### Cargar

| Herramienta | Argumentos | Que devuelve |
|---|---|---|
| `cargar_documento` | `documento_id` | `cargadas`, `a_revision` y un resultado por factura del archivo: la factura creada, o el motivo por el que quedo en revision |

### Consultar

| Herramienta | Argumentos | Que devuelve |
|---|---|---|
| `consultar_proveedor` | `proveedor` | posicion de cuenta: facturas, comprado, pagado, deuda y atraso mas viejo |
| `consultar_deudas` | - | la posicion de todos los proveedores y la deuda total |
| `consultar_facturas` | `estado`, `proveedor` | facturas con saldo y estado, saldo total y resumen por estado |
| `consultar_factura` | `factura`, `proveedor` | la factura, sus pagos y su recibo |
| `consultar_ventas` | `anio` | facturado por mes, total y cuantas ventas quedaron excluidas |
| `consultar_productos` | `buscar`, `stock_maximo` | productos con rubro, stock y precio, del stock mas bajo al mas alto |
| `consultar_calendario` | `desde`, `hasta` | vencimientos del periodo con monto, saldo, estado y recibo |
| `consultar_revision` | `tipo` | pendientes con su id, sus candidatos y el resumen por tipo |
| `consultar_mensajes` | `solo_abiertos` | la bandeja, con el id de cada mensaje |

### Actualizar

Todas guardan quien lo pidio.

| Herramienta | Argumentos | Que devuelve | Que rechaza |
|---|---|---|---|
| `registrar_pago` | `factura`, `monto_centavos`, `fecha`, `referencia`, `proveedor` | el pago, la factura con su saldo nuevo y todos sus pagos | un pago mayor al saldo, o menor o igual a cero |
| `emitir_recibo` | `factura`, `proveedor` | el recibo emitido, o el que ya existia | una factura que ya vencio |
| `ajustar_monto` | `factura`, `monto_centavos`, `motivo`, `proveedor` | monto anterior, monto nuevo y la factura | un ajuste sin motivo, o un monto negativo |
| `resolver_revision` | `pendiente_id`, `proveedor_slug`, `nota` | que se aplico y cuantos pendientes quedan | un proveedor que no esta en el catalogo, o un pendiente ya cerrado |
| `resolver_mensaje` | `mensaje_id`, `nota` | el mensaje cerrado y cuantos quedan abiertos | un mensaje que no existe |

## Lo que el agente no puede hacer

- **Crear un proveedor.** Un nombre que no resuelve contra el catalogo no se carga: el
  documento queda en la cola de revision con los candidatos que se encontraron.
- **Calcular un saldo, una deuda o un total.** Los devuelve la base ya calculados.
- **Interpretar una fecha o un monto por su cuenta.** Las fechas las lee `normalizer` y un
  monto en palabras se rechaza con el motivo.
- **Escribir sin nombre.** Sin `user`, toda herramienta que cambia algo se niega.
- **Hacerse pasar por otro.** Quien pide el cambio lo inyecta el registro, no el modelo:
  un `usuario` escrito en los argumentos se descarta.
- **Borrar.** No hay ninguna herramienta que borre.

## Errores

| Error | Cuando |
|---|---|
| `LlmError` | el servidor del modelo no contesta, o contesta algo que no es un chat completion |
| `AgentError` | falta un prompt en `prompts/` |

Que una herramienta se niegue no es una excepcion: vuelve como `{"error": "..."}` en
castellano, el modelo lo lee y se lo explica a la persona. Una herramienta que se rompe
tambien, asi una conversacion nunca se muere a la mitad.

## Invariantes

- Nunca se manda un limite de salida (`max_tokens` ni equivalente). Lo que el modelo escribe
  se guia con el prompt.
- Ningun prompt ni descripcion de herramienta vive en el codigo: todos estan en `prompts/`
  como markdown.
- La vuelta de herramientas siempre termina: cuando llega al limite de vueltas, la respuesta
  lo dice y viene con el rastro de todo lo que consulto.
- Toda respuesta viaja con el rastro de las herramientas que corrieron.
- Los montos son centavos enteros y las fechas texto ISO.

## Entorno

| Variable | Default | Para que |
|---|---|---|
| `LLM_BASE_URL` | `http://host.docker.internal:8080/v1` | el endpoint compatible con OpenAI. En Docker el host es `host.docker.internal`; corriendo local, `http://localhost:8080/v1`. Con la URL de OpenRouter funciona igual |
| `LLM_MODEL` | `gemma-4-26b-a4b-qat-q4` | que modelo pedir |
| `LLM_API_KEY` | vacia | va como `Authorization: Bearer`. llama.cpp no la necesita |
| `LLM_TEMPERATURE` | `0.2` | cuanto varia la respuesta |
| `LLM_TIMEOUT` | `120` | segundos de espera por llamada |
| `AGENT_MAX_TURNS` | `8` | cuantas vueltas de herramientas puede dar una pregunta |

El modelo local no ve imagenes. Una factura escaneada entra por el OCR de
`document_parser`, nunca como imagen al modelo.

## Depende de

`store` (la base), `normalizer` (fechas y montos), `document_parser` (los archivos),
`ingest` (el resolvedor de proveedores y la cola de revision). Ademas: `httpx`.
