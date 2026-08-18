# web

La interfaz que usa el equipo de Cordillera. React + TypeScript sobre Vite. No guarda nada:
todo lo que muestra sale de la caja `api`, y todo lo que cambia lo cambia ahí.

## Como corre

`npm install` y `npm run dev` (puerto 5173). En Docker, `docker compose up` levanta la
misma cosa contra `api`.

| Variable | Que es | Por defecto |
|---|---|---|
| `VITE_API_BASE` | de donde salen los datos y a donde va el canal en vivo | `http://localhost:8100` |

Entrada: `duenio`, `marcela` o `julian`, clave `cordillera2026`. La sesion es la cookie que
deja la api, así que todas las llamadas van con `credentials: 'include'`.

## Que secciones ve cada uno

El menu se arma con `secciones` de `/api/auth/me`. Un rol que no tiene una seccion no ve el
link, no ve las tarjetas del tablero que llevan ahí, y si escribe la URL le sale un cartel
en castellano en vez de una pantalla vacía.

## Pantallas

| Pantalla | Que muestra | De donde sale |
|---|---|---|
| Entrar | los tres usuarios y la clave | `POST /api/auth/login` |
| Tablero | primero lo que necesita atencion (vence pronto, sin recibo, ordenes olvidadas, pendientes de revision, ventas fuera del total), despues deuda por proveedor, facturacion por mes y compras por rubro | `GET /api/tablero` |
| Calendario | mes navegable, un chip por vencimiento con proveedor y saldo, color por estado de pago y marca cuando falta el recibo. Se agrega a mano y se mueve arrastrando | `GET/POST/PATCH/DELETE /api/calendario` |
| Proveedores | posicion de cada uno, cumplimiento del plazo, y el detalle con contacto, facturas, pagos, ordenes, mensajes y todas las formas en que aparece escrito el nombre | `GET /api/proveedores`, `GET /api/proveedores/{slug}` |
| Facturas | listado filtrable por estado, proveedor, formato del archivo y recibo. Detalle con pagos, recibo, archivo original y las tres acciones | `GET /api/facturas`, `GET /api/facturas/{id}`, `GET /api/facturas/{id}/archivo`, `POST .../pagos`, `POST .../recibo`, `PATCH /api/facturas/{id}` |
| Ordenes de compra | las olvidadas arriba, despues todas con filtro por estado | `GET /api/ordenes` |
| Ventas | facturacion por mes y por rubro, top productos y clientes, y el panel de las filas excluidas con el motivo de cada una | `GET /api/ventas` |
| Productos | catalogo con rubro y stock, stock bajo, productos nuevos, e historia de precios por articulo | `GET /api/productos`, `GET /api/productos/{id}/precios` |
| Revision | la cola de lo que el sistema no quiso adivinar: que llego, que sospecha y con cuanta confianza, y resolver o descartar en un clic | `GET /api/revision`, `POST /api/revision/{id}/resolver`, `POST /api/revision/{id}/descartar` |
| Mensajes | la bandeja, filtrable a los sin resolver, con la factura relacionada a mano | `GET /api/mensajes`, `POST /api/mensajes/{id}/resolver` |
| Configuracion | los parametros y el boton para actualizar desde el portal, con las ultimas pasadas | `GET/PUT /api/configuracion`, `GET /api/sync/estado`, `POST /api/sync` |

## Canal en vivo

Un solo websocket a `/ws` para toda la pagina, con reconexion sola. El indicador del
encabezado dice si esta arriba. Cada evento hace algo concreto:

| Evento | Que hace la pantalla |
|---|---|
| `calendario-cambio` | agrega, mueve o saca el chip en el acto. La api contesta la fila pelada, así que se conserva el proveedor y el saldo que ya estaban en pantalla |
| `factura-actualizada` | recarga el tablero, el listado de facturas, el proveedor abierto y el calendario |
| `recibo-emitido` | lo mismo: la marca de "sin recibo" desaparece sola |
| `revision-cambio` | actualiza el contador del menu |
| `sincronizacion-lista` | recarga ordenes, productos, mensajes, revision y el estado de la sincronizacion |

## Como esta armado

Una carpeta por pantalla en `src/features/`, y tres piezas compartidas:

- `src/lib/api.ts`: la unica puerta a la api. Ningun componente llama a `fetch`.
- `src/lib/format.ts`: los centavos enteros se muestran `$1.399.069` y las fechas ISO
  `dd/mm/aaaa`. Todo pasa por acá.
- `src/lib/useCanalVivo.tsx`: el hook del canal en vivo, con un solo socket para la pagina.

`src/ui/` son las piezas visuales sin logica (panel, tabla, chapa, modal, graficos).
`src/app/` es el armazon: sesion, menu, guardia de secciones y rutas.

## Reglas de la interfaz

- Nada tiene esquinas redondeadas. Es la regla de la casa y esta forzada en `styles/base.css`.
- Los textos estan en castellano rioplatense. Los comentarios del codigo, en ingles.
- Los montos van a la derecha con numeros de ancho fijo.
- Las tablas anchas scrollean adentro de su caja, nunca la pagina.
- Toda pantalla dice si esta cargando y muestra el error de la api tal cual viene, en
  castellano. Una pantalla en blanco sin explicacion es un bug.

## Depende de

El contrato de `api`.
