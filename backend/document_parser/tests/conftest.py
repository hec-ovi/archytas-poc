"""Test setup: the box is imported the way the rest of the backend imports it."""

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

FIXTURES = Path(__file__).parent / "fixtures"

from document_parser import DocumentParser  # noqa: E402  (needs the path above)


@pytest.fixture
def parser() -> DocumentParser:
    return DocumentParser()


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES
