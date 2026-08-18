# store

La base de datos: una sola SQLite con el esquema, los repositorios y las vistas de negocio.
Todo lo que se guarda o se consulta pasa por aca. Nadie escribe SQL afuera de esta caja.

## La decision de fondo

Nucleo relacional para lo que tiene logica de negocio, y una columna `extra` JSON en cada
tabla para lo que el cliente quiera sumar sin migrar nada. Un tipo de documento que todavia
no tiene forma vive entero en `document`, con sus campos en `parsed`.

Se eligio asi porque casi todo lo que el cliente pidio es una suma con corte: cuanto le debo
a cada proveedor, cuanto facture por mes, cuanto gasto por rubro, que vence esta semana.
Esas consultas sobre una base sin estructura se vuelven lentas de escribir y de correr; con
tablas reales es una consulta cada una, y la flexibilidad sigue estando donde hace falta.

## Reglas que valen para toda la base

- **Los montos son enteros en centavos.** Ningun float toca una cuenta.
- **Las fechas son texto ISO `YYYY-MM-DD`.**
- **Lo que se calcula no se guarda.** El saldo de una factura es su total menos los pagos
  registrados, y los dias de atraso salen de la fecha de hoy. Guardarlos es garantizar que
  algun dia digan algo distinto que la realidad.
- **Nada se pierde.** Cada fila que sirvio el portal queda cruda en `raw_record`, asi que la
  normalizacion se puede rehacer sin volver a pedir nada.

## Como se usa

```python
from store import Store
store = Store.open("/data/cordillera.db")   # crea el esquema y los usuarios si faltan
store.suppliers.positions()                 # que le debemos a cada uno
store.invoices.listing(state="parcial")     # las que estan pagas a medias
```

`Store` trae un repositorio por tema: `users`, `settings`, `suppliers`, `supplier_aliases`,
`categories`, `category_aliases`, `products`, `prices`, `invoices`, `payments`, `receipts`,
`orders`, `sales`, `messages`, `calendar`, `reviews`, `alerts`, `deliveries`, `documents`,
`raw`, `runs`.

## Lo que ofrece cada uno (lo que se usa de afuera)

| Repositorio | Metodos que importan |
|---|---|
| `suppliers` | `save`, `by_slug`, `by_cuit`, `positions`, `position`, `with_terms_compliance` |
| `supplier_aliases` | `resolve(escritura)`, `remember(id, escritura, metodo)`, `catalog_rows` |
| `categories` | `save`, `spend_by_category` |
| `products` | `save`, `by_external`, `listing`, `new_since`, `without_category`, `stock_snapshot` |
| `prices` | `record`, `for_product`, `average_by_month` |
| `invoices` | `save`, `listing`, `balance`, `due_between`, `payment_summary`, `without_receipt_due_before` |
| `payments` | `save`, `for_invoice`, `for_supplier` |
| `receipts` | `save`, `for_invoice`, `number_for(numero_factura)` |
| `orders` | `save`, `listing`, `stale`, `by_state` |
| `sales` | `save`, `flag`, `by_code`, `excluded`, `revenue_by_month`, `revenue_by_category`, `top_products`, `top_customers`, `health` |
| `messages` | `save`, `listing`, `resolve`, `open_count`, `by_kind` |
| `calendar` | `between`, `move`, `sync_from_invoice`, `for_invoice` |
| `reviews` | `raise_item`, `pending`, `resolve`, `dismiss`, `summary`, `pending_count` |
| `alerts` | `raise_event` (devuelve `(id, es_nuevo)`), `recent`, `unacknowledged`, `acknowledge` |
| `deliveries` | `record`, `failed`, `for_event` |
| `documents` | `save`, `by_hash`, `listing`, `mark` |
| `raw` | `record`, `history` |
| `runs` | `start`, `finish`, `latest`, `last_successful` |

Todos heredan de `Repository`, que da `get`, `get_by`, `all`, `count`, `insert`, `update`,
`upsert`, `delete`. Las filas salen como `dict` con las columnas JSON ya decodificadas.

## Vistas

| Vista | Que responde |
|---|---|
| `invoice_balance` | por factura: total, pagado, saldo, estado (`impaga`/`parcial`/`saldada`), si tiene recibo, dias de atraso |
| `supplier_position` | por proveedor: cuanto se le compro, cuanto se le pago, cuanto se le debe, y hace cuanto |
| `sale_valid` | solo las ventas que se pueden sumar: las duplicadas y las rotas quedan afuera |

## Accesos

Tres roles, los que pidio el cliente: `duenio` ve todo, `compras` ve proveedores, facturas,
ordenes, calendario, revision y mensajes, `ventas` ve tablero, ventas y productos.
`UserRepository.sections_for(rol)` dice que puede abrir cada uno. Las claves se guardan con
Argon2, y verificar un usuario que no existe cuesta lo mismo que uno que si.

## Errores

Los de `sqlite3`: `IntegrityError` cuando se viola una clave o una referencia. Esta caja no
define errores propios porque no tiene reglas de negocio: valida formas, no decisiones.

## Depende de

`argon2-cffi` para las claves. Nada mas.
