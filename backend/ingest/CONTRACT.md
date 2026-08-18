# ingest

Trae todo lo que publica el portal, lo normaliza y lo guarda. Es la unica caja que escribe
datos del portal en la base.

## Como se usa

```python
from ingest import IngestRunner
report = IngestRunner(store, portal_client).run(trigger="programada")
```

| Parametro | Tipo | Que es |
|---|---|---|
| `store` | `Store` | la base, de la caja `store` |
| `client` | `PortalClient` | el lector del portal, de la caja `portal_sync` |
| `trigger` | str | `programada`, `manual` o `agente`: queda registrado en la pasada |
| `with_price_history` | bool | si trae la historia de precios (100 pedidos extra, ~2 minutos) |

Devuelve un `IngestReport` con una etapa por conjunto de datos: `leidos`, `guardados`,
`resueltos`, `a_revision`, `salteados` y notas en castellano. `report.as_dict()` es lo que se
guarda en `sync_run` y lo que ve el usuario en pantalla.

## El orden importa

1. **proveedores**, del estado de cuenta. Es la unica fuente con CUIT, mail y plazo pactado,
   asi que es la autoridad contra la que se resuelve todo lo demas.
2. **productos**, con sus rubros y su historia de precios.
3. **imagenes** del catalogo.
4. **facturas**, **pagos**, **ordenes de compra**, **ventas**, **mensajes**.

Las etapas 3 en adelante solo pueden resolver si las dos primeras ya entraron.

## Que decide solo y que no

| Situacion | Que hace |
|---|---|
| Nombre de proveedor escrito distinto | lo resuelve contra el estado de cuenta y guarda la escritura como alias, asi la proxima vez es instantaneo |
| Nombre que no se parece a ninguno | queda en revision con los candidatos y su puntaje |
| Rubro escrito de varias formas | agrupa las escrituras y se queda con la mas completa |
| Producto sin rubro | lo ubica por su subrubro; si tampoco alcanza, va a revision |
| Venta repetida identica | la unifica sola |
| Venta repetida con datos distintos | no suma ninguna y va a revision con las dos filas |
| Falta uno de cantidad, precio o total | lo despeja: es aritmetica, no una suposicion. Queda anotado en la fila |
| Los tres estan y no cierran | la fila queda `rota`, fuera de todo total, con la correccion propuesta |
| Fecha que no existe | la fila queda `rota`: no se puede imputar a ningun mes |
| Venta que apunta a un producto inexistente | lo busca por precio unitario, y solo lo acepta si hay un unico candidato |

## Lo que no guarda, a proposito

- **Los dias de atraso.** El portal los recalcula contra la fecha de hoy en cada pedido; una
  copia guardada esta mal a la manana siguiente. Se calculan al leer.
- **El pagado y el saldo del portal.** El saldo sale de sumar los pagos registrados. Un total
  guardado se despega de lo que tiene debajo.
- **El libro de movimientos del estado de cuenta.** Es un saldo corriente que se reconstruye
  exacto desde facturas y pagos. Se usa para verificar, no como fuente.

Lo que si queda es cada fila cruda tal como vino, en `raw_record`, para poder rehacer la
normalizacion sin volver a pedir nada.

## Errores

Ninguno propio. Si el portal falla, la pasada termina con estado `fallida`, el motivo queda
en `report.errors`, y lo que ya se habia guardado queda guardado: toda escritura es un
upsert, asi que una pasada a medias no rompe nada y la siguiente la completa.

## Depende de

`portal_sync`, `normalizer`, `store`.
