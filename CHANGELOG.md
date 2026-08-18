# Cambios

## 1.0

Sistema completo de gestion para Ferreteria Industrial Cordillera.

- **Lectura del portal**: los nueve conjuntos de datos de SIGProv, la historia de precios por
  articulo, y las descargas con enlace firmado de 45 segundos.
- **Normalizacion deterministica**: fechas en cualquier formato, montos argentinos en
  centavos, nombres de proveedor (24 de 25 escrituras se resuelven solas contra los 8
  proveedores reales), rubros (19 escrituras agrupadas en 7), y duplicados separados entre
  los que se unifican solos y los que necesitan una persona.
- **Cola de revision**: todo lo que el sistema no resuelve queda esperando una confirmacion,
  con los candidatos y su puntaje. Una decision tomada se recuerda como alias.
- **Base SQLite** con nucleo relacional y columna `extra` JSON en cada tabla. Los saldos y los
  dias de atraso se calculan, no se guardan.
- **Lectura de documentos**: PDF con texto, PDF escaneado (OCR en espanol) y planillas
  desprolijas. Un archivo repetido se reconoce por su hash.
- **Tablero** con facturacion por mes, gasto por rubro, deuda por proveedor, vencimientos
  proximos y las ventas excluidas con su motivo.
- **Calendario de vencimientos** con arrastre para reprogramar y sincronizacion en vivo entre
  personas por WebSocket.
- **Acciones**: registrar un pago a cuenta, emitir el comprobante de recepcion y ajustar un
  monto con motivo y firma.
- **Avisos** por seis reglas, con resumen cuando una regla dispara muchos a la vez. Salen por
  WhatsApp, Telegram o bandeja local segun lo configurado.
- **Accesos por persona**: duenio, compras (Marcela) y ventas (Julian), con las secciones
  separadas del lado del servidor.
- **Agente** sobre modelo local compatible con OpenAI, con herramientas para cargar,
  consultar y actualizar, y el rastro de que hizo en cada respuesta.
