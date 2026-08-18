# portal_sync

Lee el portal viejo SIGProv: entra con usuario y clave, trae los nueve conjuntos de datos
tal como los publica, y baja los archivos adjuntos. No interpreta ni limpia nada.

## Que necesita

| Parametro | Tipo | Nota |
|---|---|---|
| `base_url` | str | `https://prueba-tecnica-portal.vercel.app` |
| `user` | str | usuario del portal |
| `password` | str | clave del portal |
| `timeout` | float | segundos, por defecto 30 |

## Que ofrece

### `PortalSession(base_url, user, password, timeout=30.0)`
Mantiene la sesion viva. El portal deja una cookie `portal_session` de 30 dias y no tiene
refresh: cuando deja de servir, vuelve a entrar sola. Usar como context manager.

- `login()` -> `None`
- `request(method, path, **kwargs)` -> `httpx.Response`, reintenta una vez re-logueando
- `close()` -> `None`

### `PortalClient(session)`
- `dataset(name)` -> `list[dict]`, las filas crudas del conjunto
- `envelope(name)` -> `dict`, la respuesta entera (algunos conjuntos traen campos extra al
  lado de la lista, por ejemplo `archivoId`)
- `all_datasets()` -> `dict[str, list[dict]]`, los nueve de una

Nombres validos y de donde salen:

| `name` | ruta | lista |
|---|---|---|
| `precios` | `/api/precios` | `productos` |
| `facturas` | `/api/facturas` | `facturas` |
| `ventas` | `/api/ventas` | `ventas` |
| `categorias` | `/api/categorias` | `categorias` |
| `ordenes_compra` | `/api/ordenes-compra` | `ordenes` |
| `estado_cuenta` | `/api/estado-cuenta` | `cuentas` |
| `comprobantes_pago` | `/api/comprobantes-pago` | `pagos` |
| `catalogo` | `/api/catalogo` | `items` |
| `mensajes` | `/api/mensajes` | `mensajes` |

### `PortalDownloader(session)`
- `signed_url(kind, item_id)` -> `str`, ruta firmada que vence
- `fetch(kind, item_id)` -> `DownloadedFile(filename, content_type, content)`

La descarga son dos pasos: `POST /api/token {kind, id}` devuelve una URL firmada
`/api/descargar/<token>` con timestamp adentro, y esa URL se sigue en el momento. La URL
vence, asi que no se guarda.

## Errores

| Error | Cuando |
|---|---|
| `PortalAuthError` | credenciales rechazadas, o la sesion sigue muerta despues de reloguear |
| `PortalUnavailable` | no responde, timeout, o 5xx |
| `PortalBadResponse` | contesto 200 con algo que no se puede leer |
| `DownloadExpired` | el link firmado fue rechazado |

## Invariantes

- Devuelve los datos como vinieron: montos como texto (`"$223.376"`), fechas como texto,
  nombres de proveedor con sus variantes. Limpiarlos es tarea de `normalizer`.
- Nunca escribe en el portal. El portal es de solo lectura salvo login y token.
- Las URL firmadas se consumen enseguida y no se persisten.

## Depende de

Nada. Solo `httpx`.
