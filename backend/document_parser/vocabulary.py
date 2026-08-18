"""The Spanish words that name each invoice field.

Every supplier writes the same six things with different words. This file is the whole
vocabulary, in one place, so growing it is an edit here and nothing else.

Two tiers per field: tier 0 names the field ("Monto total:"), tier 1 points at it from
further away ("Importe:"). A tier 1 reading is worth less confidence, so it lands under the
review threshold and a person confirms it.
"""

from __future__ import annotations

TIER_WEIGHTS = (1.0, 0.85)

# labels found in free text, at the start of a line, with or without a colon
TEXT_LABELS: dict[str, tuple[tuple[str, ...], ...]] = {
    "numero": (
        ("numero", "nro", "num", "n°", "comprobante"),
        ("factura", "factura nro", "factura numero"),
    ),
    "fecha": (
        ("fecha", "fecha de emision", "emision"),
        ("emitida el", "emitido el"),
    ),
    "vencimiento": (
        ("vencimiento", "fecha de vencimiento", "vence"),
        ("vence el", "pagar antes de", "vto"),
    ),
    "proveedor": (
        ("proveedor", "razon social", "emisor", "pagado a"),
        ("facturado por", "vendedor"),
    ),
    "total": (
        ("total", "monto total", "importe total", "total a pagar"),
        ("importe", "monto"),
    ),
}

# headers found in a spreadsheet. Matched on folded text, so "Nro." and "NRO" are the same
# word here. "precio" is deliberately absent: a price list column is not an invoice total.
COLUMN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "numero": ("numero", "nro", "num", "comprobante", "codigo", "cod", "cod venta",
               "nro factura", "numero factura", "nro comprobante"),
    "fecha": ("fecha", "fecha emision", "emision", "fecha factura", "fecha comprobante"),
    "vencimiento": ("vencimiento", "vence", "fecha vencimiento", "vto", "fecha vto"),
    "proveedor": ("proveedor", "razon social", "emisor", "vendedor"),
    "cuit": ("cuit", "cuil", "c u i t"),
    "total": ("total", "importe", "monto", "importe total", "monto total", "total factura"),
}

# how each field is named when the box has to explain itself to a person
FIELD_LABELS: dict[str, str] = {
    "numero": "numero de comprobante",
    "fecha": "fecha",
    "vencimiento": "fecha de vencimiento",
    "proveedor": "proveedor",
    "cuit": "CUIT",
    "total": "importe total",
}

# words that say the line is talking about the supplier, or about us
SUPPLIER_MARKERS = ("proveedor", "pagado a", "emisor", "razon social", "vendedor", "facturado por")
CLIENT_MARKERS = ("cliente", "recibimos de", "facturado a", "senor", "senores")
