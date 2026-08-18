# Cordillera

Sistema de gestion para Ferreteria Industrial Cordillera.

Toma los datos del portal viejo (SIGProv), los ordena, y los deja en un solo lugar donde se
entienden de un vistazo: que le debemos a cada proveedor, que vence esta semana, cuanto
vendimos, y que hay que mirar porque el sistema no quiso adivinarlo.

## Que resuelve

- **Los precios siempre actualizados**, sin que nadie entre a bajar el archivo del dia.
- **Las facturas en un solo lugar**, vengan como PDF prolijo, como foto escaneada o como
  planilla desprolija.
- **Un proveedor es un proveedor**, aunque aparezca escrito de cuatro maneras distintas.
- **Los numeros del negocio a la vista**: facturacion por mes, precios, stock, productos
  nuevos, y las ventas rotas separadas en vez de sumadas.
- **Que le debemos a cada uno y hace cuanto**, con el plazo pactado y si lo estamos
  cumpliendo.
- **Las facturas pagas a medias**, saldadas y sin tocar, cada una con su saldo real.
- **Las ordenes de compra que quedaron esperando**, para no pedir dos veces lo mismo.
- **El gasto por rubro**, con los rubros unificados.
- **Los avisos que llegan a donde se miran**: WhatsApp, no una bandeja que nadie abre.
- **Un calendario de vencimientos** que se puede mover y que dos personas ven al mismo
  tiempo.
- **Cada uno entra a lo suyo**: Marcela a compras, Julian a ventas, el duenio a todo.

## Como correrlo

Hace falta Docker y un servidor de modelo compatible con OpenAI (por defecto, el llama.cpp
que corre en la misma maquina en el puerto 8080).

```bash
git clone <este-repo> && cd archytas-poc
cp .env.example .env
docker compose up --build
```

Antes de levantar, completar en `.env` el usuario y la clave del portal SIGProv (son los que
figuran en el enunciado):

```
PORTAL_USER=...
PORTAL_PASSWORD=...
```

- Sistema: http://localhost:5173
- API: http://localhost:8100 (documentacion en http://localhost:8100/docs)

La base se crea sola en el primer arranque, vacia. Para llenarla con los datos del portal,
entrar como `duenio` y tocar "Actualizar ahora" en Configuracion, o desde la consola:

```bash
curl -s -c galletas.txt -X POST http://localhost:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"usuario":"duenio","clave":"cordillera2026"}'

curl -s -b galletas.txt -X POST http://localhost:8100/api/sync
```

La pasada tarda unos 15 segundos. Agregando `?con_historial=true` trae ademas toda la
historia de precios de cada articulo (unos 50 segundos, 100 pedidos mas al portal).

### Usuarios

| Usuario | Clave | Entra a |
|---|---|---|
| `duenio` | `cordillera2026` | todo |
| `marcela` | `cordillera2026` | proveedores, facturas, ordenes, calendario, revision, mensajes |
| `julian` | `cordillera2026` | tablero, ventas, productos |

### Sin Docker

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r backend/requirements.txt
CORDILLERA_DATA_DIR=./data .venv/bin/python -m uvicorn api.main:app --app-dir backend --port 8100
cd web && npm install && npm run dev
```

Para leer facturas escaneadas hace falta tesseract con el paquete de espanol
(`apt install tesseract-ocr tesseract-ocr-spa`). En Docker ya viene.

## Configuracion

Todo se ajusta desde `.env`. Lo que importa:

| Variable | Para que |
|---|---|
| `PORTAL_BASE_URL`, `PORTAL_USER`, `PORTAL_PASSWORD` | el portal de donde salen los datos. Usuario y clave van vacios en el ejemplo a proposito: no viajan en el repo |
| `LLM_BASE_URL`, `LLM_MODEL` | el modelo que usa el agente. Por defecto el llama.cpp local |
| `NOTIFY_CHANNELS` | `whatsapp`, `telegram` o `bandeja`. Sin credenciales, todo cae en la bandeja local |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_RECIPIENTS` | ver `backend/notify/CONTRACT.md` |
| `SECRET_KEY` | firma las sesiones. Cambiar antes de usarlo en serio |

Los parametros del negocio (cada cuanto se actualiza, con cuantos dias de anticipacion
avisar, desde que monto) se cambian desde la pantalla de Configuracion, sin tocar codigo.

## Como esta armado

El proyecto es un conjunto de cajas. Cada una hace una cosa y lleva su `CONTRACT.md`: para
usar una caja alcanza con leer su contrato.

| Caja | Que hace |
|---|---|
| `backend/portal_sync` | lee el portal: los nueve conjuntos de datos y las descargas |
| `backend/normalizer` | fechas, montos, nombres de proveedor, rubros, duplicados |
| `backend/store` | la base SQLite, los repositorios y las vistas de negocio |
| `backend/document_parser` | archivo a campos de factura, con OCR para los escaneados |
| `backend/ingest` | orquesta la pasada completa: trae, normaliza, guarda |
| `backend/agent` | el modelo con herramientas para cargar, consultar y actualizar |
| `backend/alerts` | las reglas de aviso y su programacion |
| `backend/notify` | la entrega: WhatsApp, Telegram o bandeja local |
| `backend/api` | HTTP, roles y el canal de tiempo real |
| `web` | la interfaz |

El mapa completo con las dependencias esta en `docs/INDEX.md`. Las decisiones y el por que
de cada una, en `docs/TECNICA.md`.

## Tests

```bash
.venv/bin/python -m pytest
```

Cada caja prueba lo que promete su contrato, a traves de su entrada real.
