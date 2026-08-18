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
| `agent` | LLM via OpenRouter con herramientas: cargar, consultar y actualizar documentos. Entra donde hace falta criterio. | `store`, `normalizer`, `document_parser` |
| `alerts` | Reglas de evento (vence pronto, impaga, sin recibo, orden olvidada, reclamo sin responder) y su programacion. | `store`, `notify`, `normalizer` |
| `notify` | Entrega de mensajes por canal: WhatsApp, Telegram y bandeja local. Sin credenciales cae en la bandeja. | - |
| `api` | HTTP y WebSocket. Usuarios, roles, y toda la superficie que consume la UI. | `store`, `ingest`, `agent`, `alerts`, `notify` |

## Frontend (`web/`)

| Caja | Que hace | Depende de |
|---|---|---|
| `web` | UI en Vite. Sub-cajas: tablero, proveedores, facturas, calendario, revision, configuracion. | contrato de `api` |

## Estado

En construccion. Este mapa se actualiza con cada caja que entra.
