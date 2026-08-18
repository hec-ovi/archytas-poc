"""Turning a file somebody uploaded into an invoice, or into a question for a person.

The file is read by `document_parser`: text PDF, scanned photo through OCR, or spreadsheet.
The model never sees the image and never reads the fields itself.

The supplier is resolved against the catalog with `ingest`'s resolver, the same one the sync
uses. If the name does not match anything, the document stops and goes to the review queue
with the candidates it found. It never invents a supplier: a company that does not exist in
the catalog cannot be created from a chat message.
"""

from __future__ import annotations

from typing import Any

from document_parser import REQUIRED_FIELDS, DocumentParser, DocumentParserError, ParseResult, Record
from ingest.review_queue import ReviewQueue
from store import Store

from ..errors import ToolError
from ..library import PromptLibrary
from .base import Parameter, Tool
from .lookup import SupplierLookup
from .presenters import invoice_view

# what the parser read the file with, in the words the invoice table uses
SOURCE_KINDS = {"pdf-texto": "pdf", "ocr": "pdf-escaneado", "xlsx": "excel"}


class CargarDocumento(Tool):
    name = "cargar_documento"
    needs_user = True
    parameters = (Parameter("documento_id", "integer", required=True),)

    def __init__(self, store: Store, prompts: PromptLibrary, suppliers: SupplierLookup,
                 parser: DocumentParser | None = None):
        super().__init__(store, prompts)
        self._suppliers = suppliers
        self._parser = parser or DocumentParser()
        self._review = ReviewQueue(store)

    def run(self, documento_id: object = None, usuario: str = "", **_: Any) -> dict[str, Any]:
        if not usuario:
            raise ToolError("No puedo cargar un documento sin saber quien lo pide")

        document = self._store.documents.get(int(documento_id or 0))
        if document is None:
            raise ToolError(f"No existe el documento {documento_id}")
        if document.get("invoice_id"):
            balance = self._store.invoices.balance(document["invoice_id"])
            return {"cargado": False, "motivo": "el documento ya estaba aplicado", "factura": invoice_view(balance)}
        if not document.get("stored_path"):
            raise ToolError(f"El documento {document['id']} no tiene archivo guardado")

        parsed = self._parse(document)
        self._store.documents.update(
            document["id"],
            {"parsed": parsed.as_dict(), "parser": parsed.reader, "status": "leido"},
        )

        if not parsed.records:
            return self._to_review(document, 0, "el archivo no tiene ninguna factura legible",
                                   [note.reason for note in parsed.notes])

        results = [self._one(document, parsed, record) for record in parsed.records]
        return self._close(document, parsed, results)

    def _parse(self, document: dict[str, Any]) -> ParseResult:
        try:
            return self._parser.parse(document["stored_path"])
        except DocumentParserError as error:
            self._store.documents.mark(document["id"], "fallido")
            raise ToolError(f"No se pudo leer {document['filename']}: {error}") from error

    def _one(self, document: dict[str, Any], parsed: ParseResult, record: Record) -> dict[str, Any]:
        index = record.index or 0
        missing = [name for name in REQUIRED_FIELDS if name not in record.fields or not record.fields[name].resolved]
        if missing:
            reasons = [item.reason for item in record.unreadable] or [f"no se leyeron: {', '.join(missing)}"]
            return self._to_review(document, index, f"faltan campos en {document['filename']}", reasons)

        fields = record.fields
        written = str(fields["proveedor"].value)
        supplier_id, match = self._suppliers.resolve(written)
        if supplier_id is None:
            self._review.unresolved_value(
                kind="proveedor",
                title=f"Proveedor sin identificar en {document['filename']}",
                detail=f"El documento vino a nombre de {written!r} y no coincide con ningun proveedor del catalogo",
                raw={"proveedor": written, "documento_id": document["id"], "archivo": document["filename"]},
                result=match,
                entity_kind="documento",
                entity_id=document["id"],
            )
            return {
                "estado": "en-revision",
                "motivo": f"el proveedor {written!r} no esta en el catalogo",
                "candidatos": [str(value) for value, _ in match.candidates[:3]],
            }

        number = str(fields["numero"].value)
        existing = self._store.invoices.by_number(supplier_id, number)
        if existing:
            return {
                "estado": "ya-existia",
                "factura": invoice_view(self._store.invoices.balance(existing["id"])),
            }

        invoice_id = self._store.invoices.save(
            {
                "number": number,
                "supplier_id": supplier_id,
                "issued_on": fields["fecha"].value,
                "due_on": fields["vencimiento"].value if "vencimiento" in fields else None,
                "amount_cents": int(fields["total"].value),
                "source_kind": SOURCE_KINDS.get(parsed.reader, "manual"),
                "source_file": document["filename"],
                "status": "vigente",
                "extra": {
                    "origen": "agente",
                    "documento_id": document["id"],
                    "confianza": round(record.confidence, 4),
                    "cuit_leido": fields["cuit"].value if "cuit" in fields else None,
                },
            }
        )
        invoice = self._store.invoices.get(invoice_id)
        self._store.calendar.sync_from_invoice(invoice, supplier_id)
        return {"estado": "cargada", "factura": invoice_view(self._store.invoices.balance(invoice_id))}

    def _to_review(self, document: dict[str, Any], index: int, title: str, reasons: list[str]) -> dict[str, Any]:
        self._review.conflict(
            kind="factura",
            key=f"documento-{document['id']}-{index}",
            title=title,
            detail=" / ".join(reasons),
            raw={"documento_id": document["id"], "archivo": document["filename"], "fila": index},
            candidates=[],
        )
        return {"estado": "en-revision", "motivo": title, "detalle": reasons}

    def _close(self, document: dict[str, Any], parsed: ParseResult, results: list[dict[str, Any]]) -> dict[str, Any]:
        created = [row for row in results if row["estado"] == "cargada"]
        pending = [row for row in results if row["estado"] == "en-revision"]

        status = "en-revision" if pending else "aplicado"
        invoice_id = created[0]["factura"]["id"] if len(created) == 1 and not pending else None
        self._store.documents.mark(document["id"], status, invoice_id)

        return {
            "documento": document["filename"],
            "leido_con": parsed.reader,
            "cargadas": len(created),
            "a_revision": len(pending),
            "resultados": results,
        }
