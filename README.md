# Cordillera

Sistema de gestion para Ferreteria Industrial Cordillera.

Le saca los datos al portal viejo, los ordena, y los deja en una sola pantalla que se
entiende de un vistazo: que vence esta semana, cuanto le debemos a cada proveedor, cuanto
vendimos, y que hay que mirar porque el sistema no quiso adivinarlo.

## Correrlo

Hace falta Docker. Nada mas.

```bash
cp .env.example .env
```

Abrir `.env` y completar el usuario y la clave del portal (los del enunciado):

```
PORTAL_USER=...
PORTAL_PASSWORD=...
```

Y arrancar:

```bash
docker compose up --build
```

Listo. Entrar a **http://localhost:5173**.

La primera vez se trae sola toda la informacion del portal. Tarda un minuto: mientras tanto
la pantalla ya se puede abrir y se va llenando.

## Usuarios

Los tres entran con la clave `cordillera2026`.

| Usuario | Ve |
|---|---|
| `duenio` | todo |
| `marcela` | compras: proveedores, facturas, ordenes, calendario, revision, mensajes |
| `julian` | ventas: tablero, ventas, productos |

## Que hace

- **Calendario de vencimientos.** Se arrastra para reprogramar, marca las facturas que
  todavia no tienen recibo, y si hay dos personas mirando, las dos ven los cambios al toque.
- **Proveedores.** Cuanto le compre, cuanto le pague, cuanto le debo y hace cuanto. Con el
  CUIT y el mail. El mismo proveedor aparecia escrito de 25 formas distintas: son 8.
- **Facturas.** Cuales estan saldadas, a medias y sin tocar. Se registra un pago, se emite
  el recibo y se ajusta un monto desde la misma pantalla.
- **Ventas.** Facturacion por mes y por rubro. Las ventas cargadas dos veces o con datos
  rotos **no se suman**: quedan aparte, listadas, con el motivo de cada una.
- **Revision.** Todo lo que el sistema no pudo resolver solo espera ahi, con lo que sospecha
  y cuanta confianza le tiene. Se resuelve de un clic y lo aprende para siempre.
- **Avisos.** Cuando una factura esta por vencer sin recibo, cuando hay un reclamo sin
  responder, cuando una orden quedo olvidada. Salen por WhatsApp si esta configurado, y si
  no quedan en la bandeja del sistema.
- **Subir una factura.** PDF, foto escaneada o Excel desprolijo. Lee lo que puede y avisa lo
  que no, en vez de inventarlo.
- **Preguntarle.** "Cuanto le debemos a Herramientas Cuyo", "que vence esta semana sin
  recibo". Contesta y muestra de donde saco cada numero.

## Configuracion

Lo del dia a dia se cambia desde la pantalla de **Configuracion**, sin tocar nada: cada
cuanto se actualiza, con cuantos dias de anticipacion avisar, desde que monto, y a los
cuantos dias una orden se considera olvidada.

Lo demas vive en `.env`:

| Variable | Para que | Si se deja vacia |
|---|---|---|
| `PORTAL_USER`, `PORTAL_PASSWORD` | entrar al portal | no se trae nada |
| `LLM_BASE_URL`, `LLM_MODEL` | el modelo que usa el asistente | usa el llama.cpp de esta maquina |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_RECIPIENTS` | mandar avisos por WhatsApp | los avisos quedan en la bandeja |
| `SECRET_KEY` | firma las sesiones | conviene cambiarla |

Para que WhatsApp funcione de verdad hace falta una linea de telefono dedicada y una cuenta
de Meta Business. Los pasos exactos estan en `backend/notify/CONTRACT.md`.

## Correrlo sin Docker

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r backend/requirements.txt
CORDILLERA_DATA_DIR=./data .venv/bin/python -m uvicorn api.main:app --app-dir backend --port 8100

cd web && npm install && npm run dev
```

Para leer facturas escaneadas hace falta `tesseract-ocr` y `tesseract-ocr-spa`. En Docker ya
vienen.

## Como esta armado

El proyecto son cajas. Cada una hace una cosa y lleva su `CONTRACT.md`: para usar una caja
alcanza con leer su contrato, nunca su codigo.

| Caja | Que hace |
|---|---|
| `backend/portal_sync` | lee el portal viejo |
| `backend/normalizer` | fechas, montos, nombres de proveedor, rubros, duplicados |
| `backend/store` | la base y las consultas de negocio |
| `backend/document_parser` | un archivo a campos de factura, con OCR |
| `backend/ingest` | la pasada completa: trae, normaliza, guarda |
| `backend/agent` | el asistente con sus herramientas |
| `backend/alerts` | las reglas de aviso |
| `backend/notify` | manda el mensaje |
| `backend/api` | HTTP, usuarios y tiempo real |
| `web` | la interfaz |

El mapa con las dependencias esta en `docs/INDEX.md`. Por que cada cosa se hizo asi, en
`docs/TECNICA.md`.

## Tests

```bash
.venv/bin/python -m pytest
```
