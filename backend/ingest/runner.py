"""One pass over everything the portal publishes.

Order matters. Suppliers come from the account statements because they are the authority
every other dataset gets matched against. Products come next because invoices, orders and
sales all point at them. Everything after that can only resolve if those two are already in.

Each pass is recorded: what came in, what resolved on its own, what went to a person. A pass
that fails halfway leaves what it already stored, because a partial refresh is worth more
than none and every write is an upsert.
"""

from __future__ import annotations

from typing import Any

from portal_sync.client import PortalClient
from portal_sync.errors import PortalError
from store import Store

from .report import IngestReport
from .resolvers import CategoryResolver, SupplierResolver
from .review_queue import ReviewQueue
from .stages.invoices import InvoiceStage, PaymentStage
from .stages.messages import MessageStage
from .stages.orders import PurchaseOrderStage
from .stages.products import CatalogImageStage, ProductStage
from .stages.sales import SaleStage
from .stages.suppliers import SupplierStage


class IngestRunner:
    """Pulls from the portal, normalizes, and writes. Nothing else in the system scrapes."""

    def __init__(self, store: Store, client: PortalClient):
        self._store = store
        self._client = client

    def run(self, trigger: str = "manual", with_price_history: bool = True) -> IngestReport:
        report = IngestReport()
        run_id = self._store.runs.start(trigger)

        try:
            self._run_stages(report, with_price_history)
        except PortalError as error:
            report.errors.append(f"el portal no respondio: {error}")
            self._store.runs.finish(run_id, "fallida", report.as_dict())
            return report

        self._store.runs.finish(run_id, "ok", report.as_dict())
        return report

    def _run_stages(self, report: IngestReport, with_price_history: bool) -> None:
        review = ReviewQueue(self._store)

        accounts = self._fetch("estado_cuenta", report)
        SupplierStage(self._store).run(accounts, report.stage("proveedores"))
        suppliers = SupplierResolver(self._store)
        categories = CategoryResolver(self._store)

        prices = self._fetch("precios", report)
        history = self._price_history(prices) if with_price_history else {}
        ProductStage(self._store, categories, review).run(prices, report.stage("productos"), history)

        CatalogImageStage(self._store).run(self._fetch("catalogo", report), report.stage("imagenes"))

        InvoiceStage(self._store, suppliers, review).run(self._fetch("facturas", report), report.stage("facturas"))
        PaymentStage(self._store, suppliers, review).run(
            self._fetch("comprobantes_pago", report), report.stage("pagos")
        )
        PurchaseOrderStage(self._store, suppliers, review).run(
            self._fetch("ordenes_compra", report), report.stage("ordenes de compra")
        )
        SaleStage(self._store, review).run(self._fetch("ventas", report), report.stage("ventas"))
        MessageStage(self._store, suppliers).run(self._fetch("mensajes", report), report.stage("mensajes"))

    def _fetch(self, dataset: str, report: IngestReport) -> list[dict[str, Any]]:
        """Read a dataset and keep every row exactly as it arrived before touching it."""
        rows = self._client.dataset(dataset)
        for row in rows:
            external_id = str(row.get("id") or row.get("codigo") or row.get("numero") or row.get("slug") or "")
            if external_id:
                self._store.raw.record(dataset, external_id, row)
        return rows

    def _price_history(self, products: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Price history, one request per article.

        A hundred extra requests is a lot for one pass, but it is the only place the portal
        keeps history, and without it the price chart has a single point.
        """
        history: dict[str, list[dict[str, Any]]] = {}
        for product in products:
            try:
                history[product["id"]] = self._client.price_history(product["id"])
            except PortalError:
                continue
        return history
