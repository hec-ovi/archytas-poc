# Mapa de cajas

Sistema de gestion para Ferreteria Industrial Cordillera. Chupa el portal viejo (SIGProv),
normaliza el desorden, y expone una UI unica con calendario, alertas y acciones.

Cada caja es una carpeta con su `CONTRACT.md`. Para usar una caja alcanza con leer su
contrato: nadie lee el codigo de otra caja.

## Backend (`backend/`)

| Caja | Que hace | Depende de |
|---|---|---|
| `portal_sync` | Login y lectura del portal SIGProv: 9 endpoints JSON y descarga de archivos con link efimero. Devuelve crudo. | - |
| `normalizer` | Toolkit deterministico: fechas, montos argentinos, nombres de proveedor, rubros, duplicados. Devuelve valor canonico + confianza, o marca para revision. | - |
| `store` | SQLite: esquema, repositorios, cola de revision, procedencia de cada dato. | - |
| `document_parser` | Archivo (PDF texto, PDF escaneado, Excel desprolijo) a campos de factura. OCR y extraccion asistida cuando el texto no alcanza. | `normalizer` |
| `ingest` | Orquesta: trae del portal, normaliza, guarda idempotente. Tambien procesa archivos subidos. | `portal_sync`, `normalizer`, `store`, `document_parser` |
| `agent` | El modelo con herramientas para cargar, consultar y actualizar. Corre con el rol de quien pregunta y devuelve el rastro de lo que hizo. Habla con cualquier servidor compatible con OpenAI; por defecto el llama.cpp local. | `store`, `normalizer`, `document_parser`, `ingest` |
| `alerts` | Reglas de evento (vence pronto, impaga, sin recibo, orden olvidada, reclamo sin responder) y su programacion. | `store`, `notify`, `normalizer` |
| `notify` | Entrega de mensajes por canal: WhatsApp, Telegram y bandeja local. Sin credenciales cae en la bandeja. | - |
| `api` | HTTP y WebSocket. Usuarios, roles, y toda la superficie que consume la UI. | `store`, `ingest`, `agent`, `alerts`, `notify` |

## Frontend (`web/`)

| Caja | Que hace | Depende de |
|---|---|---|
| `web` | UI en React sobre Vite. Una sub-caja por pantalla: `login`, `tablero`, `proveedores`, `facturas`, `calendario`, `ordenes`, `ventas`, `productos`, `revision`, `mensajes`, `configuracion`. Debajo, `ui` (los componentes comunes) y `lib` (cliente HTTP, formato y canal en vivo). | contrato de `api` |

## La pagina publica

`docs/index.html` (mas `docs/img/`) es una pagina sola, sin dependencias, que explica el
sistema para mostrarlo: el diagrama de las cuatro etapas, el OCR con una factura real, tres
conversaciones del agente tal como salieron, la propuesta de WhatsApp con permisos por
numero, por que CAG y no RAG, y los limites. Se publica con GitHub Pages desde esta carpeta.

## Como leerlo

Para entender o cambiar algo: este mapa, y despues el `CONTRACT.md` de la caja que toca. El
codigo de una caja solo se abre cuando es esa la que se esta cambiando.

Un cambio entra en una caja (mas este archivo, si cambia el mapa). Si una caja necesita algo
que otra no da, primero se agrega al contrato de esa otra, y despues se consume.
