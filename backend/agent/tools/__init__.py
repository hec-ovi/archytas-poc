"""The tools the agent can use: load a document, ask something, change something."""

from .agenda import ConsultarCalendario
from .base import Parameter, Tool
from .documents import CargarDocumento
from .invoices import ConsultarFactura, ConsultarFacturas, ConsultarRecibosFaltantes
from .lookup import InvoiceLookup, SupplierLookup
from .orders import ConsultarOrdenesOlvidadas
from .payments import AjustarMonto, EmitirRecibo, RegistrarPago
from .products import ConsultarProductos
from .queues import ConsultarMensajes, ConsultarRevision
from .resolutions import ResolverMensaje, ResolverRevision
from .sales import ConsultarVentas
from .suppliers import ConsultarCumplimientoPlazos, ConsultarDeudas, ConsultarProveedor

__all__ = [
    "AjustarMonto", "CargarDocumento", "ConsultarCalendario", "ConsultarCumplimientoPlazos",
    "ConsultarDeudas", "ConsultarFactura", "ConsultarFacturas", "ConsultarMensajes",
    "ConsultarOrdenesOlvidadas", "ConsultarProductos", "ConsultarProveedor",
    "ConsultarRecibosFaltantes", "ConsultarRevision", "ConsultarVentas", "EmitirRecibo",
    "InvoiceLookup", "Parameter", "RegistrarPago", "ResolverMensaje", "ResolverRevision",
    "SupplierLookup", "Tool",
]
