# Guion del video (5 minutos)

Para grabar la demo. El orden esta pensado para que cada pantalla conteste una queja del
cliente, con sus palabras.

## 0:00 - El problema, en una linea

"Ferreteria Cordillera tiene todo en un portal viejo del que solo se puede mirar. Esto es lo
que armamos."

## 0:20 - Entrar como Marcela

Login como `marcela`. Mostrar que el menu **no tiene** Tablero ni Ventas.

> "Cada uno entra a lo suyo. Marcela es compras: no ve la facturacion de la empresa."

Cambiar a `julian`: solo Tablero, Ventas y Productos. Cambiar a `duenio`: todo.

## 0:50 - El tablero

> "Cuanto facturamos por mes, como venimos, y que hay que mirar."

Senalar el panel de ventas excluidas: **24 ventas quedan afuera de los totales, con el motivo
de cada una**. Esa es la frase textual del cliente: que se le avise, no que se sumen.

## 1:30 - El calendario

La pantalla que mas pidio.

- Mes a la vista, cada vencimiento con proveedor, monto y estado de pago.
- Las que **todavia no tienen recibo** estan marcadas.
- **Arrastrar un vencimiento a otro dia**: queda guardado de donde venia.
- Abrir otra ventana al lado y mover uno: **la otra se actualiza sola**, sin refrescar.

## 2:20 - Un proveedor

Abrir Aceros Belgrano.

> "Esto le compre, esto le pague, esto le debo, y hace cuanto. Con el CUIT y el mail a mano."

Mostrar la lista de **todas las formas en que aparece escrito su nombre**: 25 escrituras para
8 proveedores, unificadas solas.

Y el cumplimiento de plazos: **Pinturerias Reunidas cumple el plazo pactado 2 de 10 veces.**
El cliente dijo que no tenia forma de saberlo.

## 3:00 - Las tres acciones

Sobre una factura:
1. Registrar un pago a cuenta (se rechaza si supera el saldo).
2. Emitir el recibo (se rechaza si la factura ya vencio: la ventana se cerro).
3. Ajustar el monto, con motivo. Queda quien, cuando y de cuanto a cuanto.

## 3:40 - Subir una factura escaneada

Subir el PDF que es una foto (`F-9936`). Mostrar que sale numero, fecha, proveedor e importe,
**y lo que no pudo leer**: "no aparece fecha de vencimiento", "los CUIT del documento son del
cliente".

> "Cuando no puede, avisa. No adivina."

Subir el mismo archivo otra vez: lo reconoce y no lo carga dos veces.

## 4:10 - La cola de revision

18 pendientes, todos decisiones reales de negocio: 12 ventas que no cierran y 6 codigos
repetidos con cantidades distintas.

Resolver uno de un clic y ver que el total del mes cambia en el acto.

## 4:30 - El aviso y el asistente

- Configuracion: cambiar "avisar con 7 dias de anticipacion" y tocar Revisar ahora.
- Mostrar el aviso que sale: **4 mensajes, no 110**, porque cuando una regla dispara muchos
  manda un resumen.
- Preguntarle al asistente: *"que facturas vencen en los proximos 30 dias y no tienen
  recibo?"* y mostrar la respuesta **con el rastro de que herramienta uso**.

## 4:50 - Cerrar

> "Todo esto sale del mismo portal que tenian. Lo que cambia es que ahora esta en un solo
> lugar, ordenado, y avisa."

---

## Numeros para tener a mano

| Dato | Valor |
|---|---|
| Escrituras de proveedor unificadas | 25 a 8 (24 automaticas) |
| Escrituras de rubro unificadas | 19 a 7 |
| Productos sin rubro despues de normalizar | 0 (eran 8) |
| Ventas leidas / que suman | 561 / 515 |
| Codigos repetidos | 27: 21 se unifican solos, 6 esperan decision |
| Facturas saldadas / a medias / sin tocar | 26 / 41 / 33 |
| Historia de precios | 553 puntos desde 2023-01-01 |
| Indice de precios | $43.650 (ene 2023) a $64.763 (hoy) |
| Avisos generados / mensajes enviados | 110 / 4 |
| Pasada completa contra el portal | 17s (48s con historia de precios) |
