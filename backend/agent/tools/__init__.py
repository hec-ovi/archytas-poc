"""The tools the agent can use: load a document, ask something, change something."""

from .agenda import ConsultarCalendario
from .base import Parameter, Tool
from .documents import CargarDocumento
from .invoices import ConsultarFactura, ConsultarFacturas
from .lookup import InvoiceLookup, SupplierLookup
from .payments import AjustarMonto, EmitirRecibo, RegistrarPago
from .products import ConsultarProductos
from .queues import ConsultarMensajes, ConsultarRevision
from .resolutions import ResolverMensaje, ResolverRevision
from .sales import ConsultarVentas
from .suppliers import ConsultarDeudas, ConsultarProveedor

__all__ = [
    "AjustarMonto", "CargarDocumento", "ConsultarCalendario", "ConsultarDeudas", "ConsultarFactura",
    "ConsultarFacturas", "ConsultarMensajes", "ConsultarProductos", "ConsultarProveedor",
    "ConsultarRevision", "ConsultarVentas", "EmitirRecibo", "InvoiceLookup", "Parameter",
    "RegistrarPago", "ResolverMensaje", "ResolverRevision", "SupplierLookup", "Tool",
]
