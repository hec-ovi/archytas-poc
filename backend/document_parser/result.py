"""What this box hands back.

One file gives one `ParseResult`. Inside it there are `Record`s: one per invoice. A PDF or
a single-invoice sheet gives exactly one record; a sheet with many rows gives one per row.

Every field of a record is either read (an `ExtractedField` with a value, a confidence and
where it came from) or flagged (an `Unreadable` with a plain reason). Nothing is guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from normalizer.result import REVIEW_THRESHOLD

# the fields this box promises to look for, in every document
INVOICE_FIELDS = ("numero", "fecha", "vencimiento", "proveedor", "cuit", "total")

# without these four an invoice cannot be loaded on its own
REQUIRED_FIELDS = ("numero", "fecha", "proveedor", "total")

KIND_INVOICE = "factura"
KIND_RECEIPT = "recibo"
KIND_TABLE = "tabla"
KIND_UNKNOWN = "desconocido"
DOCUMENT_KINDS = (KIND_INVOICE, KIND_RECEIPT, KIND_TABLE, KIND_UNKNOWN)

READER_PDF_TEXT = "pdf-texto"
READER_OCR = "ocr"
READER_SPREADSHEET = "xlsx"


@dataclass(frozen=True)
class ExtractedField:
    """One field that was read, with how sure the box is and where it came from."""

    name: str
    value: Any
    raw: str
    confidence: float
    source: str
    method: str
    reason: str = ""

    @property
    def resolved(self) -> bool:
        return self.value is not None and self.confidence >= REVIEW_THRESHOLD

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "raw": self.raw,
            "confidence": round(self.confidence, 4),
            "source": self.source,
            "method": self.method,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class Unreadable:
    """A field the box could not read, and why. Written for the person who fixes it."""

    field: str
    reason: str
    record: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"field": self.field, "reason": self.reason, "record": self.record}


@dataclass(frozen=True)
class Record:
    """One invoice worth of fields. `index` is the sheet row it came from, when it is a row."""

    fields: Mapping[str, ExtractedField]
    unreadable: tuple[Unreadable, ...] = ()
    index: int | None = None

    @property
    def confidence(self) -> float:
        """The weakest of the required fields. Zero if one of them is missing."""
        present = [self.fields[name] for name in REQUIRED_FIELDS if name in self.fields]
        if len(present) < len(REQUIRED_FIELDS):
            return 0.0
        return min(item.confidence for item in present)

    @property
    def resolved(self) -> bool:
        return self.confidence >= REVIEW_THRESHOLD

    @property
    def needs_review(self) -> bool:
        return not self.resolved

    def as_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "confidence": round(self.confidence, 4),
            "fields": {name: item.as_dict() for name, item in self.fields.items()},
            "unreadable": [item.as_dict() for item in self.unreadable],
        }


@dataclass(frozen=True)
class ParseResult:
    """Everything one file gave: what it looks like, what was read, and what was not."""

    source: str
    kind: str
    reader: str
    text: str
    records: tuple[Record, ...] = ()
    notes: tuple[Unreadable, ...] = ()

    @property
    def single(self) -> Record | None:
        """The record, when the file is one document. `None` for a sheet of many rows."""
        return self.records[0] if len(self.records) == 1 else None

    @property
    def fields(self) -> Mapping[str, ExtractedField]:
        """Shortcut for a one document file. Empty for a sheet of many rows."""
        record = self.single
        return record.fields if record else {}

    @property
    def unreadable(self) -> tuple[Unreadable, ...]:
        """Everything that could not be read: the file level notes plus every record's."""
        return (*self.notes, *(item for record in self.records for item in record.unreadable))

    @property
    def needs_review(self) -> bool:
        return bool(self.notes) or not self.records or any(r.needs_review for r in self.records)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "kind": self.kind,
            "reader": self.reader,
            "text": self.text,
            "needs_review": self.needs_review,
            "records": [record.as_dict() for record in self.records],
            "notes": [note.as_dict() for note in self.notes],
        }
