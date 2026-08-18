// Shapes returned by the api box. Amounts are always integer cents, dates ISO `YYYY-MM-DD`.

export type Seccion =
  | 'tablero' | 'proveedores' | 'facturas' | 'ordenes' | 'calendario'
  | 'ventas' | 'productos' | 'revision' | 'mensajes' | 'configuracion'

export interface Sesion {
  usuario: string
  nombre: string
  rol: 'duenio' | 'compras' | 'ventas'
  secciones: Seccion[]
}

export type EstadoPago = 'impaga' | 'parcial' | 'saldada'

/** How the invoice arrived: the format of the file the supplier actually sent. */
export type OrigenFactura = 'pdf' | 'pdf-escaneado' | 'excel' | 'portal'

export interface Factura {
  id: number
  number: string
  supplier_id: number | null
  issued_on: string | null
  due_on: string | null
  amount_cents: number
  paid_cents: number
  balance_cents: number
  payment_state: EstadoPago
  has_receipt: number
  days_overdue: number
  supplier_name: string | null
  supplier_slug?: string | null
  supplier_email?: string | null
  terms_days?: number | null
  source_kind?: OrigenFactura | string
  status?: string
  product_id?: number | null
}

export interface Pago {
  id: number
  external_id: string | null
  reference: string | null
  invoice_id: number
  supplier_id: number | null
  paid_on: string
  amount_cents: number
  created_by: string
  created_at: string
  extra: Record<string, unknown>
  invoice_number?: string
}

export interface Recibo {
  id: number
  number: string
  invoice_id: number
  issued_on: string
  issued_by: string
  pdf_path: string | null
  extra: Record<string, unknown>
}

export interface Ajuste {
  de: number
  a: number
  motivo: string
  por: string
  cuando: string
}

export interface FacturaCruda {
  id: number
  external_id: string | null
  number: string
  source_kind: OrigenFactura | string
  source_file: string | null
  status: string
  created_at: string
  updated_at: string
  extra: { ajustes?: Ajuste[]; [key: string]: unknown }
}

export interface FacturaDetalle {
  factura: Factura
  pagos: Pago[]
  recibo: Recibo | null
  cruda: FacturaCruda
}

export interface ResumenPagos { impaga: number; parcial: number; saldada: number }

export interface FacturasRespuesta { facturas: Factura[]; resumen: ResumenPagos }

export interface PosicionProveedor {
  supplier_id: number
  slug: string
  name: string
  cuit: string | null
  email: string | null
  terms_days: number | null
  invoice_count: number
  purchased_cents: number
  paid_cents: number
  owed_cents: number
  oldest_overdue_days: number | null
}

export interface Cumplimiento {
  supplier_id: number
  name: string
  terms_days: number | null
  invoice_count: number
  on_terms_count: number
}

export interface ProveedoresRespuesta {
  proveedores: PosicionProveedor[]
  cumplimiento: Cumplimiento[]
}

export interface Proveedor {
  id: number
  slug: string
  name: string
  cuit: string | null
  email: string | null
  phone: string | null
  address: string | null
  terms_days: number | null
  terms_raw: string | null
  confirmed: number
  extra: Record<string, unknown>
}

export interface Alias {
  id: number
  supplier_id: number
  spelling: string
  method: string
  confidence: number
}

export interface Orden {
  id: number
  external_id: string | null
  number: string
  supplier_id: number | null
  product_id: number | null
  ordered_on: string
  quantity: number
  estimated_cents: number
  status: string
  status_raw: string
  extra: Record<string, unknown>
  supplier_name: string | null
  supplier_slug?: string | null
  product_code?: string | null
  product_description?: string | null
  age_days: number
}

export interface Mensaje {
  id: number
  external_id: string | null
  received_on: string
  sender: string
  supplier_id: number | null
  subject: string
  body: string
  invoice_id: number | null
  product_id: number | null
  kind: string
  resolved: number
  resolved_by: string | null
  resolved_at: string | null
  extra: Record<string, unknown>
  supplier_name: string | null
  invoice_number: string | null
  product_code: string | null
}

export interface ProveedorDetalle {
  proveedor: Proveedor
  posicion: PosicionProveedor | null
  alias: Alias[]
  facturas: Factura[]
  pagos: Pago[]
  ordenes: Orden[]
  mensajes: Mensaje[]
}

export interface EventoCalendario {
  id: number
  title: string
  on_date: string
  kind: 'vencimiento' | 'recordatorio' | string
  invoice_id: number | null
  supplier_id: number | null
  amount_cents: number | null
  note: string
  moved_from: string | null
  created_by: string
  updated_at: string
  extra: Record<string, unknown>
  supplier_name: string | null
  invoice_number: string | null
  balance_cents: number | null
  payment_state: EstadoPago | null
  has_receipt: number | null
  days_ahead: number
}

export interface CalendarioRespuesta {
  desde: string
  hasta: string
  eventos: EventoCalendario[]
}

export interface VentasPorMes { month: string; sale_count: number; revenue_cents: number; units: number }
export interface VentasPorRubro { category: string; revenue_cents: number; sale_count: number }
export interface ProductoTop { code: string; description: string; revenue_cents: number; units: number }
export interface ClienteTop { customer: string; revenue_cents: number; sale_count: number }
export interface SaludVentas { [estado: string]: { count: number; cents: number } }

export interface VentaExcluida {
  id: number
  code: string
  sold_on: string | null
  product_id: number | null
  customer: string | null
  quantity: number | null
  unit_cents: number | null
  total_cents: number | null
  status: string
  status_note: string
  row_hash: string
  extra: { crudo?: Record<string, string>; reparaciones?: string[] }
  product_code: string | null
  product_description: string | null
}

export interface VentasRespuesta {
  por_mes: VentasPorMes[]
  por_rubro: VentasPorRubro[]
  productos_top: ProductoTop[]
  clientes_top: ClienteTop[]
  salud: SaludVentas
  excluidas: VentaExcluida[]
}

export interface GastoPorRubro {
  category: string
  slug: string | null
  product_count: number
  purchased_cents: number
}

export interface Sincronizacion {
  id: number
  started_at: string
  finished_at: string | null
  trigger: string
  status: string
  summary: {
    guardados?: number
    a_revision?: number
    errores?: string[]
    etapas?: EtapaSync[]
  }
}

export interface EtapaSync {
  etapa: string
  leidos: number
  guardados: number
  resueltos: number
  a_revision: number
  salteados: number
  notas: string[]
}

export interface Tablero {
  ventas_por_mes: VentasPorMes[]
  ventas_por_rubro: VentasPorRubro[]
  productos_top: ProductoTop[]
  clientes_top: ClienteTop[]
  salud_ventas: { validas: { count: number; cents: number }; excluidas: SaludVentas; excluidas_total: number }
  estado_pagos: ResumenPagos
  deuda_por_proveedor: PosicionProveedor[]
  gasto_por_rubro: GastoPorRubro[]
  vencen_pronto: Factura[]
  sin_recibo: Factura[]
  ordenes_olvidadas: Orden[]
  pendientes_revision: number
  mensajes_abiertos: number
  productos_nuevos: Producto[]
  ultima_sincronizacion: Sincronizacion | null
}

export interface Producto {
  id: number
  external_id: string | null
  code: string
  description: string
  category_id: number | null
  subcategory: string | null
  price_cents: number
  stock: number
  image_url: string | null
  first_seen: string | null
  last_seen: string | null
  extra: Record<string, unknown>
  category_name?: string | null
  category_slug?: string | null
}

export interface FilaStock {
  id: number
  code: string
  description: string
  stock: number
  price_cents: number
  category: string
}

export interface ProductosRespuesta {
  productos: Producto[]
  sin_rubro: Producto[]
  stock: FilaStock[]
  nuevos: Producto[]
  precio_promedio_por_mes: { month: string; products: number; average_cents: number }[]
}

export interface PrecioHistorico {
  taken_on: string
  price_cents: number
  stock: number
  source: string
}

export interface PreciosRespuesta { producto: Producto; historial: PrecioHistorico[] }

export interface CandidatoRevision {
  valor: string | number
  puntaje: number
  nota?: string
  fila?: Record<string, string>
}

export interface PendienteRevision {
  id: number
  kind: string
  dedupe_key: string
  title: string
  detail: string
  raw: Record<string, unknown>
  candidates: CandidatoRevision[] | Record<string, never>
  entity_kind: string | null
  entity_id: number | null
  status: string
  created_at: string
}

export interface RevisionRespuesta {
  pendientes: PendienteRevision[]
  resumen: { kind: string; n: number }[]
}

export interface OrdenesRespuesta {
  ordenes: Orden[]
  olvidadas: Orden[]
  por_estado: { status: string; n: number; cents: number }[]
  dias_para_olvidada: number
}

export interface MensajesRespuesta {
  mensajes: Mensaje[]
  por_tipo: { kind: string; n: number; open: number }[]
  abiertos: number
}

export interface Parametro {
  key: string
  value: number | string
  label: string
  updated_at: string
  updated_by: string
}

export interface ConfiguracionRespuesta { configuracion: Parametro[] }

export interface EstadoSync {
  ultima_ok: Sincronizacion | null
  pasadas: Sincronizacion[]
  cada_horas: number
}

export type EventoVivo =
  | 'calendario-cambio'
  | 'factura-actualizada'
  | 'recibo-emitido'
  | 'revision-cambio'
  | 'sincronizacion-lista'

export interface MensajeVivo {
  evento: EventoVivo
  datos: Record<string, unknown>
}
