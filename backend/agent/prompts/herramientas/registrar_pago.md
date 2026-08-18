Registra un pago a cuenta sobre una factura y devuelve el saldo que queda. Un pago mayor al
saldo se rechaza. Queda anotado quien lo pidio.

## factura
El numero de la factura que se paga, como `F-7797`.

## monto_centavos
El monto pagado en centavos enteros: doscientos mil pesos son 20000000.

## fecha
La fecha del pago, como la dijo la persona. Si no dice nada, es hoy.

## referencia
La referencia del pago (transferencia, cheque, numero de operacion), si la persona la dio.

## proveedor
El proveedor de esa factura. Solo hace falta si el numero de factura puede ser de mas de uno.
