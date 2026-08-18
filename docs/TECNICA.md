# Documentacion tecnica

Como se abordo cada problema del cliente y por que se penso asi. El orden es el del relato
del cliente, no el del codigo.

Antes de escribir una linea se hizo un relevamiento del portal y de los datos. Casi todas las
decisiones de abajo salen de ahi, no de suponer.

---

## Lo primero: que es realmente el portal

El portal (SIGProv) es una aplicacion Next.js con login por cookie. Detras hay nueve
endpoints JSON de solo lectura, y un mecanismo de descarga en dos pasos: se pide un token y
se sigue una URL firmada.

Lo que se encontro relevando, y que cambio el diseño:

- **El enlace de descarga vive 45 segundos.** No se puede guardar ni encolar: se pide justo
  antes de bajar el archivo.
- **Hay una ruta con historia de precios que no figura en ningun menu**: `/api/precios/{id}`
  devuelve todos los precios que tuvo un articulo. Sin eso, la evolucion de precios habria
  que construirla tomando una foto por dia y no habria nada que mostrar hasta dentro de
  meses. Con eso, hay historia desde 2023 el primer dia.
- **Sin sesion, algunos endpoints contestan 200 con el HTML del login adentro.** Confiar en
  el codigo de estado mete un formulario de login en la base creyendo que son datos. Se
  detectan las tres formas: 307, 401 y 200 con HTML.
- **El portal no acepta escrituras.** Solo `/api/login` y `/api/token` aceptan POST, y
  ninguno modifica nada. Todo lo que el cliente quiere hacer (recibos, pagos, ajustes) vive
  necesariamente de este lado.

## La base: nucleo relacional con lugar para lo imprevisto

Se penso en una base sin estructura fija, para que el cliente pueda sumar propiedades o tipos
de documento sin migrar nada. Se descarto en esa forma pura por una razon concreta: casi todo
lo que el cliente pidio es una suma con corte (cuanto le debo a cada proveedor, cuanto
facture por mes, cuanto gasto por rubro, que vence esta semana). Esas consultas sobre una
base sin estructura se vuelven caras de escribir y de correr, y el dia alcanzaba justo.

Lo que quedo: tablas reales para lo que tiene logica de negocio, **una columna `extra` JSON en
cada tabla** para propiedades nuevas, y **una tabla `document`** donde entra cualquier tipo de
documento que todavia no tiene forma, con sus campos en `parsed`. Se puede sumar un remito,
una nota de credito o un campo nuevo sin tocar el esquema, y los tableros siguen siendo una
consulta cada uno.

Tres reglas que valen para toda la base:

- **Los montos son enteros en centavos.** Ningun float toca una cuenta.
- **Lo que se calcula no se guarda.** El saldo de una factura es su total menos los pagos
  registrados; los dias de atraso salen de la fecha de hoy. Guardarlos es garantizar que
  algun dia digan algo distinto que la realidad.
- **Nada se pierde.** Cada fila que sirvio el portal queda cruda en `raw_record`, asi que la
  normalizacion se puede rehacer sin volver a pedir nada, y siempre hay respuesta a "de donde
  sale este numero".

---

## El problema de los precios

> "Solo podes entrar con tu usuario, navegar hasta la seccion de precios y descargar el
> archivo del dia."

La caja `portal_sync` entra con la cuenta que dieron, lee los nueve conjuntos y baja
archivos. `ingest` corre la pasada completa y `alerts` la programa cada tantas horas, con el
intervalo como parametro editable desde la pantalla de Configuracion.

El portal actualiza dos veces por dia, asi que el valor por defecto es cada 12 horas. Tambien
hay un boton para actualizar en el momento: esperar a que corra el programa cuando ya sabes
que algo cambio es exactamente la friccion de la que se quejaban.

La foto diaria de stock se guarda ademas de la historia de precios, porque **el stock no
tiene historia en ningun lado** del portal. Sin tomar la foto, "que paso con el stock" no
tiene respuesta nunca.

## El problema de las facturas

> "Algunos un PDF prolijo, otros un PDF que en realidad es una foto escaneada, otros
> directamente un Excel armado a las apuradas."

Los numeros reales del portal: **29 Excel, 25 PDF con texto, 46 PDF escaneados.** Casi la
mitad necesita OCR, asi que no era un caso de borde que se pudiera dejar afuera.

`document_parser` decide el tipo de archivo **por los bytes, no por la extension**, y toma
tres caminos:

- **PDF con texto**: busca cada campo por su etiqueta.
- **PDF escaneado**: rasteriza con poppler y lee con tesseract en espanol. Verificado sobre
  la factura escaneada real: sale numero, fecha, proveedor e importe.
- **Planilla**: busca la fila de encabezado donde este, saltea filas vacias, y mapea columnas
  por nombre aproximado. Tambien lee la planilla que es una sola factura en formato
  etiqueta/valor.

Lo importante es lo que hace cuando **no** puede: nunca elige. En el recibo de prueba hay dos
importes y en una planilla hay dos columnas de importe candidatas; en los dos casos deja el
campo marcado con los dos valores a la vista en vez de quedarse con uno. Y detecta que los
CUIT que aparecen en la factura son del cliente, no del proveedor, asi que no los toma.

Una factura subida dos veces se reconoce por el hash del archivo y no se carga de nuevo.

## El problema de los proveedores

> "En el sistema el mismo me aparece escrito de tres o cuatro formas distintas."

Este resulto ser el problema central, porque **es el unico puente entre los conjuntos de
datos**: el CUIT existe solamente en el estado de cuenta, en ningun otro lado. Si el nombre no
se resuelve, no hay forma de saber que una factura y un pago son del mismo proveedor.

Los numeros reales: **25 escrituras distintas para 8 proveedores**.

La estrategia es determinista primero:

1. El estado de cuenta es la autoridad: trae los 8 proveedores reales con CUIT, mail,
   telefono y plazo pactado.
2. Cada nombre se compara sacando acentos y puntuacion, descartando formas societarias
   (`S.R.L.`, `SA`, `SACIF`) y conectores (`del`, `de`, `la`), expandiendo abreviaturas
   comunes, y ordenando los tokens. Dos escrituras del mismo nombre terminan con la misma
   firma.
3. Lo que no coincide exacto se puntua combinando solapamiento de tokens con parecido de
   caracteres. Una palabra que empieza a otra cuenta casi como la misma palabra, porque asi
   es como la gente abrevia: `Pint. Reunidas` es `Pinturerias Reunidas`.

**Resultado: 24 de 25 se resuelven solas.** La que queda es `Sistema SIGProv`, que es el bot
del portal y correctamente no se toma por proveedor: inventarlo habria creado una novena
empresa de la nada.

Y cada escritura resuelta **queda guardada como alias**. La proxima pasada la resuelve al
instante, y a una persona nunca se le pregunta dos veces lo mismo.

En la pantalla del proveedor se muestran todas las formas en que aparece escrito. El problema
del cliente no era solo tener el dato unificado: era no saber si dos facturas eran del mismo
proveedor. Mostrarlo resuelto es parte de la respuesta.

## El problema de no ver nada

> "Hay ventas cargadas dos veces por error... necesitamos que se nos avise cuales son, no que
> se sumen como si fueran validas."

Esta frase define el criterio de todo el sistema, asi que se siguio al pie de la letra.

Lo que se encontro en las 561 ventas: **27 codigos repetidos**, y 10 de esos pares solo se ven
si se normaliza la clave, porque llegan como `"V-1189"` y como `" v-1189 "`. Agrupar por el
texto literal pierde mas de un tercio de las repeticiones.

Repetido no es una sola cosa, y tratarlas igual es como se rompen los totales:

- **21 grupos son la misma fila cargada dos veces.** Se unifican solos, sin molestar a nadie.
- **6 grupos tienen el mismo codigo con cantidades distintas.** Nadie puede decidir eso desde
  los datos: **no se suma ninguna** y van a la cola de revision con las dos filas a la vista.

Para las filas rotas se distinguio lo que es aritmetica de lo que es adivinar:

- Si falta **uno solo** de cantidad, precio o total y los otros dos estan, el que falta no es
  una suposicion: es el unico valor posible. Se despeja y queda anotado en la fila.
- Si los tres estan y **no cierran**, la fila queda marcada, fuera de todo total, con la
  correccion propuesta para que una persona la acepte con un clic.
- Una fecha que no existe (`31/02/2025`) deja la fila afuera: no se puede imputar a ningun
  mes.
- Una venta que apunta a un producto inexistente se busca por precio unitario, y **solo se
  acepta si hay un unico candidato**.

De 561 filas quedan **515 que se pueden sumar**. Las 24 que no estan listadas en pantalla con
el motivo de cada una. Un total nunca es mas chico que la realidad sin decir por que.

## El problema de los rubros

> "Cada uno cargo las categorias como se le ocurrio, y ahora tengo el mismo rubro escrito de
> cinco maneras y varios productos sin nada cargado."

Aca no habia autoridad contra la cual comparar: nadie escribio nunca la lista real de rubros.
Asi que se descubre desde las escrituras mismas, agrupandolas por parecido, y **de cada grupo
queda como nombre bueno la escritura mas completa** (y entre iguales, la que no esta toda en
mayusculas: el cliente lee esto en pantalla).

**19 escrituras se agrupan en 7 rubros reales.**

Para los 8 productos sin rubro se uso algo que ya estaba en los datos: la subcategoria esta
siempre cargada, no tiene variantes, y mapea limpio a un rubro. Asi que un producto sin rubro
se ubica por su subrubro. **Los 100 productos quedan con rubro**, y el gasto por rubro no
tiene un cajon de "otros".

El `slug` que ya trae el portal no servia: unifica mayusculas pero no abreviaturas, asi que
deja separados justamente los casos de los que el cliente se queja.

## El problema de los pagos a medias

> "No tengo manera de ver de una cuales estan saldadas, cuales van por la mitad y cuales no se
> tocaron."

El saldo de una factura **nunca se guarda**: se calcula como el total menos la suma de los
pagos registrados. Una factura puede tener varios pagos (15 tienen dos), y el estado sale de
ahi: saldada, parcial o impaga.

Los numeros hoy: **26 saldadas, 41 a medias, 33 sin tocar.**

Se guarda como referencia lo que dice el portal, pero no se usa para nada: un total guardado
se despega de los pagos que tiene debajo, y ese es exactamente el momento en que el cliente
deja de confiar en el sistema.

## El problema de las compras que se pierden

> "Me pasa de pedir dos veces lo mismo porque nadie se acordaba del primer pedido."

Las ordenes se cargan con su estado normalizado y, sobre todo, **con su edad**. Lo que la
pantalla muestra primero no es la lista: son las ordenes abiertas que llevan mas dias de los
configurados esperando. Esas son las que se piden dos veces.

El sistema tambien avisa cuando encuentra un estado que el portal usa y no estaba previsto,
en vez de meterlo en una bolsa de "otros" en silencio. Asi aparecieron dos estados que el
relevamiento inicial no habia visto.

## El problema de los avisos que nadie mira

> "Nadie entra ahi, asi que nos enteramos cuando el proveedor llama enojado."

La bandeja del portal tiene 55 mensajes de cuatro tipos, y el portal no los etiqueta: el tipo
esta escondido en el prefijo del id. Se separan **12 reclamos de proveedores** (los que
cuestan plata cuando se ignoran) de las 27 avisos de vencimiento y los 16 de stock.

"Leido en el portal" no es lo mismo que "resuelto". Un mensaje sigue abierto hasta que alguien
lo cierra aca, con su nombre.

Y el aviso sale de la bandeja: la caja `notify` entrega por **WhatsApp**, que es donde el
cliente si mira. Un evento se dispara una sola vez (tiene clave de deduplicacion) y la entrega
se guarda aparte, asi que un mensaje que fallo se reintenta sin volver a disparar el evento.

**Que necesita el cliente para que WhatsApp funcione**, verificado contra la documentacion de
Meta al dia de hoy:

1. Una linea de telefono dedicada para el sistema, primero borrada de las apps de WhatsApp y
   WhatsApp Business.
2. Una cuenta de Meta Business con una app de WhatsApp, que da el `PHONE_ID` y el token (de
   usuario de sistema: el del panel vence en 24 horas).
3. Una plantilla de utilidad aprobada en `es_AR`, redactada estrictamente transaccional o
   Meta la reclasifica como marketing y la cobra como tal.
4. Opt-in por escrito de cada numero. La politica no hace excepcion con los empleados.

Cuesta centavos por mes a este volumen. Desde el 2026-10-01 las respuestas libres dentro de la
ventana de 24 horas dejan de ser gratis, por eso la caja esta construida sobre plantillas y no
sobre esa ventana.

**Sin credenciales el sistema igual funciona**: los avisos caen en una bandeja local y se ven
en pantalla. Tambien hay canal de Telegram, que no necesita tramite de aprobacion. Se cambia
con una variable de entorno.

## El problema de no tener control

> "Queremos poder hacer esas cosas nosotros mismos desde un solo lugar."

Tres acciones, cada una con su regla:

- **Registrar un pago a cuenta.** Se rechaza si supera el saldo.
- **Emitir un recibo.** Se rechaza si la factura ya vencio, porque el recibo se emite hasta la
  fecha de vencimiento. Pasado eso es una conversacion con el proveedor, no un boton.
- **Ajustar un monto.** Pide un motivo y guarda quien, cuando y de cuanto a cuanto. Un monto
  que cambia sin el nombre de nadie es como se muere la confianza en un sistema.

Y los parametros (cada cuanto se actualiza, cuantos dias antes avisar, desde que monto, a los
cuantos dias una orden esta olvidada) se editan desde la pantalla de Configuracion.

## El problema de los accesos

> "Hoy entramos todos con el mismo usuario y eso ya no me sirve."

Tres usuarios con clave propia (Argon2) y tres roles. Cada ruta declara la seccion a la que
pertenece, y un rol que no la tiene recibe 403 **sepa o no la URL**: no alcanza con esconder
el link del menu.

| Rol | Entra a |
|---|---|
| `duenio` | todo |
| `compras` (Marcela) | proveedores, facturas, ordenes, calendario, revision, mensajes |
| `ventas` (Julian) | tablero, ventas, productos |

Son tres roles y no una matriz de permisos porque tres es lo que se pidio, y una matriz que
nadie mantiene termina dando permiso a todo.

## El problema de las fechas

> "Necesitamos un calendario visual... y que si dos personas lo estan mirando al mismo tiempo,
> ambas vean los cambios en el momento."

Cada factura con vencimiento entra al calendario, mas lo que se agregue a mano. Se puede mover
una fecha arrastrandola, y **queda guardado de donde venia**: "esto se reprogramo" es
informacion que hoy se pierde.

Una fecha que una persona movio a mano **no se pisa en la proxima sincronizacion**. Si el
sistema le corrigiera la fecha al dia siguiente, nadie volveria a usarlo.

El tiempo real es un WebSocket con difusion en el proceso. Alcanza porque todo corre en un
contenedor; si algun dia corre en varios, es la unica pieza que hay que mover a un bus
compartido, y es un archivo.

## El problema de los recibos

> "Nos gustaria que el calendario nos muestre que facturas ya tienen su recibo generado y
> cuales todavia no, y que si se acerca la fecha de una que sigue sin generar, nos avise antes
> de que sea tarde."

El recibo es el comprobante de recepcion, no un pago: son dos cosas distintas y estan en dos
tablas distintas. En el calendario cada vencimiento muestra si ya tiene el suyo.

La regla de aviso mas importante del sistema es justamente esta: **factura que se acerca al
vencimiento y todavia no tiene recibo**. Es la unica que tiene una ventana que se cierra: una
vez pasada la fecha, el recibo ya no se puede emitir.

---

## El agente, y donde no se lo usa

El agente corre sobre un modelo local (llama.cpp con Gemma 4, en la misma maquina, sin costo
por token) y sirve para lo que necesita criterio: leer una factura que llego suelta, contestar
"cuanto le debemos a Herramientas Cuyo", ejecutar "registra 200 mil de pago en la F-7797".

La division es deliberada y es la decision mas importante del diseño: **todo lo que puede
decidir una regla ya lo decidio una regla.** El modelo no calcula un saldo, no interpreta una
fecha, no inventa un proveedor. Llama a herramientas que hacen esas cosas bien. Un modelo que
normaliza 561 filas de ventas es caro, lento y, lo peor, distinto cada vez que corre: el
cliente no podria auditar por que un mes cambio.

Cada respuesta del agente viene con el rastro de que herramientas uso y con que argumentos.
Sin eso no es una herramienta de gestion, es una opinion.

La configuracion es compatible con OpenAI, asi que apuntarlo a OpenRouter u otro proveedor es
cambiar dos variables de entorno.

---

## Lo que quedo afuera

Con honestidad, que es lo que se pidio:

- **La ventana de 45 segundos del enlace de descarga** esta respetada, pero no se bajan los
  100 archivos de factura en cada pasada: se bajan cuando alguien abre la factura. Bajar todo
  siempre serian 100 pedidos extra por pasada para archivos que casi nadie mira.
- **La historia de precios son 100 pedidos** al portal, asi que es opcional en la pasada
  (`con_historial=true`). Corre bien, pero tarda unos minutos y no hace falta dos veces por
  dia.
- **El OCR no corre en cualquier maquina**: necesita tesseract con el paquete de espanol. En
  la imagen de Docker viene; fuera de Docker, si falta, el sistema lo dice claramente en vez
  de fallar raro.
- **Productos nuevos** se calcula desde la primera vez que el sistema vio el producto, porque
  el portal no tiene fecha de alta en ningun lado. La primera pasada se fecha en 2023-01-01
  para no marcar los 100 productos como nuevos el primer dia.
- **El tiempo real es de un solo proceso.** Con varias replicas hay que poner un bus.
- **WhatsApp esta implementado y probado contra el endpoint real de Meta**, pero para que
  salga un mensaje de verdad hacen falta la linea, la cuenta y la plantilla aprobada, que son
  del cliente. Mientras tanto los avisos se ven en la bandeja local.
