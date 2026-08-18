# normalizer

Toolkit deterministico que convierte valores sucios en valores canonicos. Fechas en
cualquier formato, montos argentinos, nombres de proveedor escritos de N maneras, rubros
cargados a mano, y registros que llegaron dos veces.

No usa modelos ni red. Todo es codigo y reglas, asi que el mismo dato siempre da el mismo
resultado y se puede explicar por que.

## La regla de oro

Nunca adivina. Cada funcion devuelve un `Normalized` que dice si resolvio, con cuanta
confianza, y con que metodo. Si no llega al umbral, el valor queda sin resolver y viaja con
sus candidatos para que una persona confirme.

## Que ofrece

### `Normalized`
| Campo | Tipo | Que es |
|---|---|---|
| `raw` | str | lo que entro |
| `value` | Any | lo canonico, o `None` |
| `confidence` | float | 0 a 1 |
| `method` | str | como se resolvio (`exact`, `signature`, `fuzzy`, `iso`, `dot-thousands`, ...) |
| `reason` | str | por que no resolvio, cuando no resolvio |
| `candidates` | tuple[(valor, puntaje)] | lo mas parecido que encontro |
| `resolved` | bool | `value` presente y `confidence >= 0.90` |
| `needs_review` | bool | lo contrario |
| `as_dict()` | dict | para guardar o mandar por HTTP |

### `parse_date(raw) -> Normalized`
Entra cualquier cosa con forma de fecha (texto, `date`, `datetime`, serial de Excel), sale
`YYYY-MM-DD`. Reconoce ISO, `dd/mm/yyyy`, `dd-mm-yy`, `20260503`, `3 de mayo de 2026`,
`3-may-2026`. Argentina escribe el dia primero: `03/05/2026` es 3 de mayo. Cuando las dos
lecturas son posibles resuelve dia primero con confianza 0.93, para que quede el rastro de
que fue una decision.

### `parse_amount(raw) -> Normalized`, `format_amount(cents) -> str`
Entra `"$223.376"`, `"$1.234,56"`, `"1,399,069.50"`, `"($1.200)"`, numeros. Sale un entero
de centavos. Decide cual separador es decimal mirando cual viene ultimo y cuantos digitos
lo siguen. `format_amount` hace el camino inverso al formato que lee el cliente.

### `CatalogMatcher(entries)` con `CatalogEntry(key, name, aliases)`
Resuelve un texto contra un conjunto chico de entidades reales. Se usa para proveedores y
para rubros.

- `match(raw) -> Normalized` con `value` = la `key` de la entidad
- `add(entry)`, `learn_alias(key, spelling)`, `entries`

Tres desenlaces: `>= 0.90` se aplica solo; entre `0.72` y `0.90` va a revision con el
candidato adjunto; por debajo va a revision como entidad nueva posible.

### `DuplicateFinder(key_field, compare_fields=None)`
- `scan(rows) -> list[DuplicateGroup]`

`DuplicateGroup(key, kind, rows, differing_fields, count)` con `kind`:
- `IDENTICAL`: la misma fila cargada dos veces, se colapsa sola
- `CONFLICTING`: el mismo codigo con contenido distinto, no se suma ninguna y va a revision

### Utilidades de texto
`fold(s)`, `signature(s)`, `similarity(a, b)`. `signature` da una clave estable: saca
acentos, puntuacion y sufijos societarios (`S.R.L.`, `SA`), expande abreviaturas comunes
(`Distrib.` a `distribuidora`) y ordena los tokens. Dos formas de escribir un mismo nombre
comparten firma.

## Errores

| Error | Cuando |
|---|---|
| `UnknownCatalog` | se pidio resolver contra un catalogo que no se cargo |

Los valores que no se pueden leer no son un error: vuelven como `Normalized` sin resolver.

## Invariantes

- Determinista: sin red, sin modelos, sin reloj (salvo lo que se le pasa).
- Los montos salen siempre en centavos enteros. Ningun float toca una cuenta.
- Las fechas salen siempre como texto ISO.
- Nada se resuelve por debajo de 0.90 sin que una persona lo confirme.

## Depende de

Nada. Solo la biblioteca estandar.
