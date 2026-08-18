"""Everything the rest of the system needs from the database, in one place."""

from .accounts import ROLE_SECTIONS, SettingRepository, UserRepository
from .agenda import CalendarRepository
from .alerts import AlertRepository, DeliveryRepository
from .base import Repository
from .bootstrap import bootstrap
from .catalog import (
    CategoryAliasRepository,
    CategoryRepository,
    PriceHistoryRepository,
    ProductRepository,
)
from .database import Database, dumps, loads
from .documents import DocumentRepository, content_hash
from .invoices import InvoiceRepository, PaymentRepository, ReceiptRepository
from .messages import MessageRepository
from .orders import PurchaseOrderRepository
from .passwords import hash_password, verify_password
from .provenance import RawRecordRepository, SyncRunRepository
from .review import ReviewRepository
from .sales import SaleRepository
from .suppliers import SupplierAliasRepository, SupplierRepository


class Store:
    """One handle carrying every repository, so callers pass a single object around."""

    def __init__(self, db: Database):
        self.db = db
        self.users = UserRepository(db)
        self.settings = SettingRepository(db)
        self.suppliers = SupplierRepository(db)
        self.supplier_aliases = SupplierAliasRepository(db)
        self.categories = CategoryRepository(db)
        self.category_aliases = CategoryAliasRepository(db)
        self.products = ProductRepository(db)
        self.prices = PriceHistoryRepository(db)
        self.invoices = InvoiceRepository(db)
        self.payments = PaymentRepository(db)
        self.receipts = ReceiptRepository(db)
        self.orders = PurchaseOrderRepository(db)
        self.sales = SaleRepository(db)
        self.messages = MessageRepository(db)
        self.calendar = CalendarRepository(db)
        self.reviews = ReviewRepository(db)
        self.alerts = AlertRepository(db)
        self.deliveries = DeliveryRepository(db)
        self.documents = DocumentRepository(db)
        self.raw = RawRecordRepository(db)
        self.runs = SyncRunRepository(db)

    @classmethod
    def open(cls, path: str) -> "Store":
        db = Database(path)
        bootstrap(db)
        return cls(db)

    def close(self) -> None:
        self.db.close()


__all__ = [
    "Store", "Database", "bootstrap", "ROLE_SECTIONS", "Repository",
    "hash_password", "verify_password", "content_hash", "dumps", "loads",
]
