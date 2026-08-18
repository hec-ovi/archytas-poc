"""Feeding a document in by hand.

"Each supplier sends invoices however they can: some a neat PDF, others a PDF that is
really a scanned photo, others an Excel thrown together in a hurry. We need all of this to
land in one place, tidy, without anything getting duplicated, and if something cannot be
resolved on its own, to be told instead of guessed wrong."

So an upload is two steps, never one. First the file is read and what was found is shown,
with the confidence of each field and what could not be read. Then a person applies it. The
system never turns a file into an invoice on its own when it is not sure.

The same file uploaded twice is recognised by its hash and does not become a second invoice.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from document_parser import DocumentParser
from ingest.resolvers import SupplierResolver
from store import Store, content_hash

from ..deps import get_hub, get_settings, get_store
from ..realtime import Hub
from ..security import requires

router = APIRouter(prefix="/api/documentos", tags=["documentos"])

REQUIRED = ("numero", "fecha", "proveedor", "total")


@router.get("")
def listing(estado: str | None = None, store: Store = Depends(get_store),
            user: dict = Depends(requires("facturas"))) -> dict:
    return {"documentos": store.documents.listing(status=estado)}


@router.get("/{document_id}")
def detail(document_id: int, store: Store = Depends(get_store),
           user: dict = Depends(requires("facturas"))) -> dict:
    document = store.documents.get(document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese documento")
    return {"documento": document}


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload(archivo: UploadFile = File(...), store: Store = Depends(get_store),
                 settings=Depends(get_settings), user: dict = Depends(requires("facturas"))) -> dict:
    content = await archivo.read()
    digest = content_hash(content)

    known = store.documents.by_hash(digest)
    if known:
        return {"documento": known, "nuevo": False, "aviso": "Este archivo ya se habia subido antes"}

    inbox = settings.data_dir / "documentos"
    inbox.mkdir(parents=True, exist_ok=True)
    stored_path = inbox / f"{digest[:16]}-{archivo.filename}"
    stored_path.write_bytes(content)

    result = DocumentParser().parse(stored_path)
    proposal = _proposal(store, result)
    # a field read at low confidence is still a field: it can be applied, but a person should
    # see it first. That is different from a field that is missing, which blocks the load.
    needs_eyes = proposal["falta"] or result.needs_review

    document_id = store.documents.save(
        {
            "kind": result.kind,
            "filename": archivo.filename or stored_path.name,
            "mime": archivo.content_type or "",
            "stored_path": str(stored_path),
            "content_hash": digest,
            "parsed": {**result.as_dict(), "propuesta": proposal},
            "parser": result.reader,
            "status": "en-revision" if needs_eyes else "leido",
            "uploaded_by": user["usuario"],
        }
    )
    return {"documento": store.documents.get(document_id), "nuevo": True}


@router.post("/{document_id}/aplicar", status_code=status.HTTP_201_CREATED)
async def apply(document_id: int, store: Store = Depends(get_store), hub: Hub = Depends(get_hub),
                user: dict = Depends(requires("facturas"))) -> dict:
    document = store.documents.get(document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe ese documento")
    if document.get("invoice_id"):
        return {"factura_id": document["invoice_id"], "nuevo": False}

    proposal = document.get("parsed", {}).get("propuesta", {})
    if proposal.get("falta"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Falta resolver antes de cargarlo: {', '.join(proposal['falta'])}",
        )

    supplier_id = proposal["proveedor_id"]
    number = proposal["numero"]
    existing = store.invoices.by_number(supplier_id, number)
    if existing:
        store.documents.mark(document_id, "aplicado", existing["id"])
        return {"factura_id": existing["id"], "nuevo": False,
                "aviso": f"La factura {number} de ese proveedor ya estaba cargada"}

    invoice_id = store.invoices.save(
        {
            "number": number,
            "supplier_id": supplier_id,
            "issued_on": proposal["fecha"],
            "due_on": proposal.get("vencimiento") or _due_from_terms(store, supplier_id, proposal["fecha"]),
            "amount_cents": proposal["total"],
            "source_kind": document.get("parser", "manual"),
            "source_file": document.get("stored_path"),
            "status": "vigente",
            "extra": {"cargada_por": user["usuario"], "documento_id": document_id},
        }
    )
    store.documents.mark(document_id, "aplicado", invoice_id)

    invoice = store.invoices.get(invoice_id)
    store.calendar.sync_from_invoice(invoice, supplier_id)
    await hub.broadcast("factura-actualizada", {"id": invoice_id, "estado": "impaga"})
    return {"factura_id": invoice_id, "nuevo": True, "factura": store.invoices.balance(invoice_id)}


def _proposal(store: Store, result) -> dict:
    """What we would load, and what is missing before we can.

    The supplier is resolved against the eight real companies. A name that does not match
    is not invented as a new supplier: it is reported as missing, because a supplier
    appearing out of nowhere is exactly the mess this system exists to end.
    """
    fields = result.fields
    missing = [name for name in REQUIRED if name not in fields]

    supplier_id = None
    supplier_note = ""
    if "proveedor" in fields:
        supplier_id, match = SupplierResolver(store).resolve(str(fields["proveedor"].value))
        if supplier_id is None:
            missing.append("proveedor")
            candidates = ", ".join(f"{key} ({score:.0%})" for key, score in match.candidates[:2])
            supplier_note = (
                f"No se pudo identificar a {fields['proveedor'].value!r} entre los proveedores conocidos."
                + (f" Se parece a: {candidates}." if candidates else "")
            )
        else:
            supplier = store.suppliers.get(supplier_id)
            supplier_note = f"Identificado como {supplier['name']} ({match.method})"

    return {
        "numero": str(fields["numero"].value) if "numero" in fields else None,
        "fecha": fields["fecha"].value if "fecha" in fields else None,
        "vencimiento": fields["vencimiento"].value if "vencimiento" in fields else None,
        "total": fields["total"].value if "total" in fields else None,
        "proveedor_texto": fields["proveedor"].value if "proveedor" in fields else None,
        "proveedor_id": supplier_id,
        "proveedor_nota": supplier_note,
        "falta": sorted(set(missing)),
        "ilegible": [u.as_dict() if hasattr(u, "as_dict") else str(u) for u in result.unreadable],
    }


def _due_from_terms(store: Store, supplier_id: int | None, issued_on: str | None) -> str | None:
    """A missing due date is filled from the term agreed with that supplier, not invented."""
    if not supplier_id or not issued_on:
        return None
    supplier = store.suppliers.get(supplier_id)
    if not supplier or not supplier.get("terms_days"):
        return None
    from datetime import timedelta
    return (date.fromisoformat(issued_on) + timedelta(days=int(supplier["terms_days"]))).isoformat()
