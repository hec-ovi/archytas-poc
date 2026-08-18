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
- `price_history(product_id)` -> `list[dict]` con `{fecha, precio}`, toda la historia de
  precios de un articulo. Es la unica parte del portal que guarda historia, y no esta
  enlazada desde el menu.
- `product_detail(product_id)` -> `dict`, el articulo con su historial adentro
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
`/api/descargar/<token>`, y esa URL se sigue en el acto. **El enlace vive 45 segundos**, asi
que se pide justo antes de bajar y nunca se guarda.

Los ocho `kind` que el portal acepta, cada uno con su idea de que es un id:

| `kind` | `id` |
|---|---|
| `precios` | el `archivoId` de `/api/precios`, hoy `lista-precios-actual` |
| `historial` | id de producto, `p1` |
| `factura` | id de factura, `f89` |
| `ventas` | el `archivoId` de `/api/ventas`, hoy `ventas-historico` |
| `categoria` | slug de rubro, `ferreteria-gral` |
| `cuenta` | slug de proveedor, `aceros-belgrano-sa` |
| `recibos` | el texto `listado` |
| `recibo` | id de pago, `pago-f7-1` |

Las facturas llegan en tres formas: Excel (29), PDF con texto (25) y PDF que es una foto
escaneada (46). Casi la mitad necesita OCR.

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
- Nunca escribe en el portal. Solo `/api/login` y `/api/token` aceptan POST, y ninguno
  modifica datos: el portal es de solo lectura.
- Una respuesta sin sesion puede volver como 307, como 401, o como 200 con el HTML del
  login adentro. Las tres se tratan como sesion caida, asi que nunca entra un formulario
  de login a la base creyendo que son datos.
- Las URL firmadas se consumen enseguida y no se persisten.

## Depende de

Nada. Solo `httpx`.
