"""Closed error set for the document_parser box.

Only two things are errors: a file this box does not know how to open, and a file it
cannot read at all. Everything else (a field it could not find, an OCR engine that is not
installed) comes back inside the result, never as an exception.
"""


class DocumentParserError(Exception):
    """Base for everything this box raises."""


class UnsupportedFormat(DocumentParserError):
    """The bytes are neither a PDF nor an xlsx workbook."""


class UnreadableFile(DocumentParserError):
    """The file is missing, empty, or too broken to open."""
