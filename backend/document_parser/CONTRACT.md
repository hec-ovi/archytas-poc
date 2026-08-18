# document_parser

Entra un archivo (PDF con texto, PDF escaneado, planilla xlsx) y salen campos de factura:
numero, fecha, vencimiento, proveedor, CUIT e importe total. Cada campo viaja con su
confianza y con el lugar exacto de donde salio (`linea 3 del texto`, `celda B4`,
`columna 'Fecha', fila 12`).

El tipo de archivo se decide por los bytes, nunca por la extension.

## La regla de oro

Nunca adivina. Cada campo esta leido o esta marcado, y lo marcado explica por que en
castellano. Cuando hay dos candidatos para el mismo campo (dos columnas de importe, dos
fechas en el mismo recibo) no elige ninguno: lo marca con los dos valores a la vista.

## Como se usa

```python
from document_parser import DocumentParser

resultado = DocumentParser().parse("F-8411.pdf")
resultado.fields["total"].value        # 58123000 (centavos)
resultado.unreadable                   # lo que no se pudo leer, con motivo
```

## Que ofrece

### `DocumentParser().parse(path) -> ParseResult`
Unico punto de entrada. `path` es texto o `Path`.

### `ParseResult`
| Campo | Tipo | Que es |
|---|---|---|
| `source` | str | nombre del archivo |
| `kind` | str | `factura`, `recibo`, `tabla`, `desconocido` |
| `reader` | str | `pdf-texto`, `ocr`, `xlsx` |
| `text` | str | el texto crudo que se leyo, para que una persona vea lo mismo |
| `records` | tuple[Record] | uno por documento. Una planilla de muchas filas da uno por fila |
| `notes` | tuple[Unreadable] | problemas del archivo entero (falta una columna, falta tesseract) |
| `single` | Record o None | el unico registro, cuando el archivo es un solo documento |
| `fields` | dict[str, ExtractedField] | atajo a los campos de `single`. Vacio si son muchas filas |
| `unreadable` | tuple[Unreadable] | `notes` mas lo marcado en cada registro |
| `needs_review` | bool | hay notas, no hay registros, o algun registro no llega a 0.90 |
| `as_dict()` | dict | para guardar o mandar por HTTP |

### `Record`
Una factura. `fields` (los campos leidos), `unreadable` (los que no), `index` (la fila de
la planilla, o `None` si el archivo entero es un documento), `confidence` (el mas debil de
los campos requeridos, 0.0 si falta alguno), `resolved`, `needs_review`, `as_dict()`.

### `ExtractedField`
`name`, `value`, `raw` (lo que decia el documento), `confidence`, `source` (de donde salio),
`method` (como lo resolvio el normalizer), `reason` (la salvedad, cuando la hay).

### `Unreadable`
`field` (el campo, o `documento` si el problema es del archivo), `reason` (en castellano),
`record` (la fila, cuando aplica).

## Los seis campos

| Campo | Valor | Nota |
|---|---|---|
| `numero` | str | como figura, en mayusculas: `F-8411` |
| `fecha` | str | ISO `YYYY-MM-DD` |
| `vencimiento` | str | ISO `YYYY-MM-DD` |
| `proveedor` | str | el nombre tal cual. Resolverlo contra el catalogo es tarea de `normalizer` |
| `cuit` | str | `NN-NNNNNNNN-N`, y solo si el documento dice que es del proveedor |
| `total` | int | centavos |

Requeridos para cargar una factura sola: `numero`, `fecha`, `proveedor`, `total`.

## Que hace con cada formato

**PDF con texto.** Busca cada campo por su etiqueta al principio de una linea
(`Numero:`, `Fecha de emision:`, `Pagado a:`, `Monto total:`). Las etiquetas viven todas en
`vocabulary.py`.

**PDF escaneado.** Si el PDF no tiene capa de texto, se rasteriza (poppler `pdftoppm`, y si
no esta, la imagen embebida del PDF) y se lee con tesseract en espanol. Despues sigue el
mismo camino que un PDF de texto.

**Planilla xlsx.** Dos formas. Si encuentra una fila de encabezado que nombra tres campos o
mas, cada fila de abajo es un documento: busca el encabezado donde este (no asume la fila 1)
y saltea las filas vacias del medio. Si no la encuentra, la lee como etiqueta y valor
(`Numero | F-7797` en dos celdas). Si tampoco, dice que la planilla no es de facturas.

## Confianza

Sale de `normalizer` (una fecha ambigua vale 0.93) y se descuenta segun de donde vino:

| Situacion | Peso |
|---|---|
| etiqueta o columna que nombra el campo | 1.00 |
| etiqueta o columna lejana (`Importe` para el total, encabezado con error de tipeo) | 0.85 |
| todo lo que salio de OCR | 0.95 |

Debajo de 0.90 el dato no se aplica solo: va a revision, igual que en `normalizer`.

El digito verificador del CUIT se calcula pero nunca sirve para descartar: si no cierra, el
CUIT vuelve igual con confianza 0.75 y el motivo, porque un digito que no cierra es la forma
tipica de un error de OCR.

## Errores

| Error | Cuando |
|---|---|
| `UnsupportedFormat` | los bytes no son ni PDF ni planilla xlsx |
| `UnreadableFile` | el archivo no existe, esta vacio, o esta demasiado roto para abrirlo |

Que falte tesseract no es un error: el resultado vuelve con `reader = ocr`, sin texto, y una
nota que lo dice.

## Invariantes

- Cada uno de los seis campos aparece exactamente una vez por registro: leido en `fields`,
  o marcado en `unreadable` del registro o en `notes` del archivo.
- Un archivo de un solo documento siempre devuelve un registro, aunque no se haya podido
  leer nada.
- Los montos salen en centavos enteros y las fechas en texto ISO, como los devuelve
  `normalizer`. Ningun float toca una cuenta.
- Sin red y sin modelos de lenguaje. Lo unico externo son tesseract y poppler.

## Entorno

| Variable | Default | Para que |
|---|---|---|
| `TESSERACT_BIN` | `tesseract` | binario de OCR. La imagen Docker lo trae con el paquete `spa` |
| `PDFTOPPM_BIN` | `pdftoppm` | rasterizador de poppler |

## Depende de

`normalizer` (fechas, montos, texto). Ademas: `pdfplumber`, `pypdf`, `openpyxl`,
`pytesseract`.
