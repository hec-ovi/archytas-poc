"""document_parser: un archivo entra, campos de factura salen.

    from document_parser import DocumentParser
    resultado = DocumentParser().parse("factura.pdf")
"""

from .errors import DocumentParserError, UnreadableFile, UnsupportedFormat
from .parser import DocumentParser
from .result import (
    INVOICE_FIELDS,
    REQUIRED_FIELDS,
    ExtractedField,
    ParseResult,
    Record,
    Unreadable,
)

__all__ = [
    "DocumentParser",
    "DocumentParserError",
    "ExtractedField",
    "INVOICE_FIELDS",
    "ParseResult",
    "REQUIRED_FIELDS",
    "Record",
    "Unreadable",
    "UnreadableFile",
    "UnsupportedFormat",
]
