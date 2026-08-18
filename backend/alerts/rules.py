"""The six reasons this system interrupts someone, in the order they matter.

The client already had an inbox full of warnings and read none of them. So a rule earns its
place only if missing it costs money or repeats work: the receipt that can no longer be
issued, the invoice already overdue, the big one about to fall, the order that gets placed
twice, the claim nobody answered, and the data waiting for a person to confirm it.
"""

from __future__ import annotations

from store import Store

from .event import AVISO, URGENTE, AlertEvent
from .rule import Rule
from .settings import AlertSettings
from .texts import TextLibrary

# an order is open until the portal says it arrived or was cancelled
CLOSED_ORDERS = ("recibida", "anulada")
NO_SUPPLIER = "proveedor sin identificar"


class MissingReceiptRule(Rule):
    """The one that costs money: the receipt can only be issued up to the due date."""

    name = "recibo_faltante"
    severity = URGENTE
    text = "recibo_faltante"
    entity_kind = "factura"

    def evaluate(self, store: Store, settings: AlertSettings) -> list[AlertEvent]:
        clock = settings.clock
        events = []
        for invoice in store.invoices.without_receipt_due_before(clock.plus_days(settings.recibo_dias_antes)):
            due_on = invoice["due_on"]
            if due_on < clock.today:  # the window already closed, the overdue rule owns it
                continue
            events.append(
                self._event(
                    key=f"{invoice['id']}:{due_on}",
                    entity_id=invoice["id"],
                    due_on=due_on,
                    params={
                        "numero": invoice["number"],
                        "proveedor": self.words(invoice.get("supplier_name"), NO_SUPPLIER),
                        "monto": self.money(invoice["amount_cents"]),
                        "vencimiento": clock.pretty(due_on),
                        "plazo": clock.phrase(due_on),
                    },
                )
            )
        return events


class OverdueInvoiceRule(Rule):
    """Past its due date and still owing. This is the call the supplier makes."""

    name = "factura_vencida"
    severity = URGENTE
    text = "factura_vencida"
    entity_kind = "factura"

    def evaluate(self, store: Store, settings: AlertSettings) -> list[AlertEvent]:
        clock = settings.clock
        events = []
        for invoice in store.invoices.listing():
            due_on = invoice["due_on"]
            if not due_on or due_on >= clock.today or invoice["balance_cents"] <= 0:
                continue
            events.append(
                self._event(
                    key=f"{invoice['id']}:{due_on}",
                    entity_id=invoice["id"],
                    due_on=due_on,
                    params={
                        "numero": invoice["number"],
                        "proveedor": self.words(invoice.get("supplier_name"), NO_SUPPLIER),
                        "monto": self.money(invoice["amount_cents"]),
                        "saldo": self.money(invoice["balance_cents"]),
                        "vencimiento": clock.pretty(due_on),
                        "dias": str(clock.days_since(due_on)),
                    },
                )
            )
        return events


class LargeInvoiceDueRule(Rule):
    """About to fall and big enough to plan for. Small ones stay in the screen, not the phone."""

    name = "factura_por_vencer"
    severity = AVISO
    text = "factura_por_vencer"
    entity_kind = "factura"

    def evaluate(self, store: Store, settings: AlertSettings) -> list[AlertEvent]:
        clock = settings.clock
        window = store.invoices.due_between(clock.today, clock.plus_days(settings.aviso_dias_antes))
        events = []
        for invoice in window:
            if invoice["amount_cents"] < settings.aviso_monto_minimo or invoice["balance_cents"] <= 0:
                continue
            due_on = invoice["due_on"]
            events.append(
                self._event(
                    key=f"{invoice['id']}:{due_on}",
                    entity_id=invoice["id"],
                    due_on=due_on,
                    params={
                        "numero": invoice["number"],
                        "proveedor": self.words(invoice.get("supplier_name"), NO_SUPPLIER),
                        "monto": self.money(invoice["amount_cents"]),
                        "saldo": self.money(invoice["balance_cents"]),
                        "vencimiento": clock.pretty(due_on),
                        "plazo": clock.phrase(due_on),
                    },
                )
            )
        return events


class StaleOrderRule(Rule):
    """An order nobody closed is an order somebody places again."""

    name = "orden_vieja"
    severity = AVISO
    text = "orden_vieja"
    entity_kind = "orden"

    def evaluate(self, store: Store, settings: AlertSettings) -> list[AlertEvent]:
        clock = settings.clock
        events = []
        for order in store.orders.listing():
            if str(order.get("status") or "").strip().lower() in CLOSED_ORDERS:
                continue
            age = clock.days_since(order.get("ordered_on"))
            if age is None or age <= settings.orden_vieja_dias:
                continue
            events.append(
                self._event(
                    key=f"{order['id']}:{order['ordered_on']}",
                    entity_id=order["id"],
                    params={
                        "numero": order["number"],
                        "proveedor": self.words(order.get("supplier_name"), NO_SUPPLIER),
                        "fecha": clock.pretty(order["ordered_on"]),
                        "dias": str(age),
                        "estado": self.words(order.get("status"), "sin estado"),
                        "monto": self.money(order.get("estimated_cents")),
                    },
                )
            )
        return events


class OpenClaimRule(Rule):
    """The inbox nobody opens. A claim sitting there is the supplier already angry."""

    name = "reclamo_sin_responder"
    severity = AVISO
    text = "reclamo_sin_responder"
    entity_kind = "mensaje"

    def evaluate(self, store: Store, settings: AlertSettings) -> list[AlertEvent]:
        clock = settings.clock
        events = []
        for message in store.messages.listing(only_open=True):
            if message.get("kind") != "reclamo":
                continue
            events.append(
                self._event(
                    key=str(message["id"]),
                    entity_id=message["id"],
                    params={
                        "proveedor": self.words(
                            message.get("supplier_name") or message.get("sender"), NO_SUPPLIER
                        ),
                        "fecha": clock.pretty(message.get("received_on")),
                        "asunto": self.words(message.get("subject"), "sin asunto"),
                        "factura": self.words(message.get("invoice_number"), "sin factura"),
                    },
                )
            )
        return events


class ReviewQueueRule(Rule):
    """One digest a day for the whole queue. One alert per pending item is the old inbox again."""

    name = "revision_pendiente"
    severity = AVISO
    text = "revision_pendiente"

    def evaluate(self, store: Store, settings: AlertSettings) -> list[AlertEvent]:
        pending = store.reviews.pending_count()
        if not pending:
            return []
        detail = ", ".join(f"{row['kind']}: {row['n']}" for row in store.reviews.summary())
        return [
            self._event(
                key=settings.today,
                params={"cantidad": str(pending), "detalle": detail or "sin detalle"},
            )
        ]


# priority order: the first rule that speaks about an entity is the one that gets sent
RULE_CLASSES = (
    MissingReceiptRule,
    OverdueInvoiceRule,
    LargeInvoiceDueRule,
    StaleOrderRule,
    OpenClaimRule,
    ReviewQueueRule,
)


def default_rules(texts: TextLibrary | None = None) -> list[Rule]:
    """Every rule, sharing one text library so the files are read once."""
    library = texts or TextLibrary()
    return [rule_class(library) for rule_class in RULE_CLASSES]
