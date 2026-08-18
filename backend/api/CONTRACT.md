# api

La superficie HTTP del sistema: todo lo que consume la UI y lo que usa el agente. Abre la
base, arma la sesion de cada persona, y decide que puede ver cada rol.

## Como corre

`uvicorn api.main:app`. Al arrancar crea la base si no existe, la siembra con los tres
usuarios y los parametros por defecto, y levanta el canal de tiempo real.

Variables de entorno en `.env.example`. Las que importan: `CORDILLERA_DATA_DIR`,
`PORTAL_*`, `SECRET_KEY`, `LLM_*`.

## Acceso

`POST /api/auth/login` con `{usuario, clave}` deja una cookie firmada de 7 dias.
Usuarios sembrados: `marcela` (compras), `julian` (ventas), `duenio` (todo). Clave inicial
`cordillera2026` para los tres.

Cada ruta declara la seccion a la que pertenece. Un rol que no la tiene recibe 403, sepa o
no la URL.

| Rol | Secciones |
|---|---|
| `duenio` | todas |
| `compras` | proveedores, facturas, ordenes, calendario, revision, mensajes |
| `ventas` | tablero, ventas, productos |

## Rutas

### Acceso
| Metodo | Ruta | Que hace |
|---|---|---|
| POST | `/api/auth/login` | entra y deja la cookie |
| POST | `/api/auth/logout` | sale |
| GET | `/api/auth/me` | quien soy y que secciones tengo |

### Tablero (`tablero`)
| GET | `/api/tablero` | todo el panorama en una sola llamada: ventas por mes y por rubro, deuda por proveedor, que vence pronto, que no tiene recibo, ordenes olvidadas, pendientes de revision, productos nuevos |

### Proveedores (`proveedores`)
| GET | `/api/proveedores` | posicion de cada uno y cumplimiento de plazos |
| GET | `/api/proveedores/{slug}` | el proveedor con sus facturas, pagos, ordenes, mensajes y todas las formas en que aparece escrito |

### Facturas (`facturas`)
| GET | `/api/facturas?estado=&proveedor=` | listado. `estado` es `impaga`, `parcial` o `saldada` |
| GET | `/api/facturas/{id}` | la factura, sus pagos y su recibo |
| POST | `/api/facturas/{id}/pagos` | registra un pago a cuenta. `{monto_centavos, fecha?, referencia?}`. Rechaza un pago mayor al saldo |
| POST | `/api/facturas/{id}/recibo` | emite el comprobante de recepcion. Rechaza si la factura ya vencio |
| PATCH | `/api/facturas/{id}` | ajusta el monto. `{monto_centavos, motivo}`. Guarda quien, cuando y por que |

### Calendario (`calendario`)
| GET | `/api/calendario?desde=&hasta=` | los vencimientos del periodo, con saldo, estado de pago y si tiene recibo |
| POST | `/api/calendario` | agrega un vencimiento a mano |
| PATCH | `/api/calendario/{id}` | lo mueve de fecha y recuerda de donde venia |
| DELETE | `/api/calendario/{id}` | borra uno agregado a mano. Los de factura no se borran desde aca |

### Ventas y productos (`ventas`, `productos`)
| GET | `/api/ventas` | por mes, por rubro, top productos y clientes, y las excluidas con su motivo |
| GET | `/api/productos` | listado, sin rubro, stock, nuevos, precio promedio por mes |
| GET | `/api/productos/{id}/precios` | la historia de precios del articulo |

### Operacion
| GET | `/api/ordenes` | ordenes, las olvidadas, y el conteo por estado (`ordenes`) |
| GET | `/api/mensajes?abiertos=` | la bandeja (`mensajes`) |
| POST | `/api/mensajes/{id}/resolver` | cierra un mensaje (`mensajes`) |
| GET | `/api/revision?tipo=` | la cola de lo que el sistema no quiso adivinar (`revision`) |
| POST | `/api/revision/{id}/resolver` | aplica la decision y la recuerda para siempre (`revision`) |
| POST | `/api/revision/{id}/descartar` | lo saca sin cambiar nada (`revision`) |
| GET | `/api/configuracion` | los parametros (`configuracion`) |
| PUT | `/api/configuracion/{key}` | cambia uno. `{valor}` (`configuracion`) |
| GET | `/api/alertas` | avisos recientes, sin ver, y entregas fallidas |
| POST | `/api/alertas/{id}/visto` | marca un aviso como visto |

### Sincronizacion
| GET | `/api/sync/estado` | la ultima pasada buena y las diez ultimas |
| POST | `/api/sync?con_historial=` | lanza una pasada y contesta enseguida (`configuracion`) |

### Salud
| GET | `/api/salud` | vive, y cuantas facturas, ventas y paginas abiertas hay |

## Tiempo real

`WS /ws`. Canal de una sola direccion: el servidor avisa, la pagina escucha. Los mensajes
son `{evento, datos}`:

| Evento | Cuando |
|---|---|
| `calendario-cambio` | alguien agrego, movio o borro un vencimiento |
| `factura-actualizada` | se registro un pago o se ajusto un monto |
| `recibo-emitido` | se emitio un comprobante de recepcion |
| `revision-cambio` | se resolvio o descarto un pendiente |
| `sincronizacion-lista` | termino una pasada, con su resumen |

## Formatos

- **Los montos viajan en centavos enteros**, siempre, con el sufijo `_centavos` en el
  nombre. La UI decide como mostrarlos.
- **Las fechas viajan como texto ISO `YYYY-MM-DD`.**
- Los errores son `{"detail": "texto en castellano"}` con el codigo HTTP que corresponde.

## Errores

| Codigo | Cuando |
|---|---|
| 401 | sin sesion o vencida |
| 403 | el rol no tiene esa seccion |
| 404 | no existe lo que se pidio |
| 409 | la accion no corresponde: recibo de una factura vencida, borrar un vencimiento de factura |
| 400 | el dato no cierra: un pago mayor al saldo |

## Depende de

`store`, `ingest`, `portal_sync`, `normalizer`.
