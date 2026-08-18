// The single door to the api box. No component calls fetch on its own.

import { API_BASE } from './config'
import { ApiError } from './errors'
import type {
  CalendarioRespuesta, ConfiguracionRespuesta, EstadoSync, EventoCalendario,
  Factura, FacturaDetalle, FacturasRespuesta, MensajesRespuesta, OrdenesRespuesta,
  PreciosRespuesta, ProductosRespuesta, ProveedorDetalle, ProveedoresRespuesta,
  RevisionRespuesta, Sesion, Tablero, VentasRespuesta,
} from './types'

type Metodo = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

async function request<T>(metodo: Metodo, path: string, body?: unknown): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: metodo,
      credentials: 'include',
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'No se puede conectar con el servidor. Revisa que este encendido.')
  }

  if (!response.ok) {
    throw new ApiError(response.status, await detalle(response))
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

async function detalle(response: Response): Promise<string> {
  try {
    const data = await response.json()
    if (typeof data?.detail === 'string') return data.detail
    if (Array.isArray(data?.detail)) return data.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('. ')
  } catch {
    /* the body was not json */
  }
  if (response.status === 401) return 'La sesion venció. Volvé a entrar.'
  if (response.status === 403) return 'Tu usuario no tiene acceso a esta seccion.'
  return `Error ${response.status} del servidor`
}

function query(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

export const api = {
  acceso: {
    entrar: (usuario: string, clave: string) =>
      request<Sesion>('POST', '/api/auth/login', { usuario, clave }),
    salir: () => request<{ ok: boolean }>('POST', '/api/auth/logout'),
    quienSoy: () => request<Sesion>('GET', '/api/auth/me'),
  },

  tablero: () => request<Tablero>('GET', '/api/tablero'),

  proveedores: {
    listar: () => request<ProveedoresRespuesta>('GET', '/api/proveedores'),
    detalle: (slug: string) => request<ProveedorDetalle>('GET', `/api/proveedores/${encodeURIComponent(slug)}`),
  },

  facturas: {
    listar: (filtros: { estado?: string; proveedor?: number } = {}) =>
      request<FacturasRespuesta>('GET', `/api/facturas${query(filtros)}`),
    detalle: (id: number) => request<FacturaDetalle>('GET', `/api/facturas/${id}`),
    pagar: (id: number, datos: { monto_centavos: number; fecha?: string; referencia?: string }) =>
      request<{ factura: Factura }>('POST', `/api/facturas/${id}/pagos`, datos),
    emitirRecibo: (id: number) =>
      request<{ recibo: unknown; nuevo: boolean }>('POST', `/api/facturas/${id}/recibo`),
    ajustar: (id: number, datos: { monto_centavos: number; motivo: string }) =>
      request<{ factura: Factura }>('PATCH', `/api/facturas/${id}`, datos),
  },

  calendario: {
    listar: (desde: string, hasta: string) =>
      request<CalendarioRespuesta>('GET', `/api/calendario${query({ desde, hasta })}`),
    agregar: (datos: {
      titulo: string; fecha: string; nota?: string
      factura_id?: number | null; proveedor_id?: number | null; monto_centavos?: number | null
    }) => request<{ evento: EventoCalendario }>('POST', '/api/calendario', datos),
    mover: (id: number, fecha: string) =>
      request<{ evento: EventoCalendario }>('PATCH', `/api/calendario/${id}`, { fecha }),
    borrar: (id: number) => request<{ ok: boolean }>('DELETE', `/api/calendario/${id}`),
  },

  ventas: () => request<VentasRespuesta>('GET', '/api/ventas'),

  productos: {
    listar: () => request<ProductosRespuesta>('GET', '/api/productos'),
    precios: (id: number) => request<PreciosRespuesta>('GET', `/api/productos/${id}/precios`),
  },

  ordenes: () => request<OrdenesRespuesta>('GET', '/api/ordenes'),

  mensajes: {
    listar: (abiertos = false) => request<MensajesRespuesta>('GET', `/api/mensajes${query({ abiertos })}`),
    resolver: (id: number) => request<{ abiertos: number }>('POST', `/api/mensajes/${id}/resolver`),
  },

  revision: {
    listar: (tipo?: string) => request<RevisionRespuesta>('GET', `/api/revision${query({ tipo })}`),
    resolver: (id: number, decision: Record<string, unknown>) =>
      request<{ aplicado: string; pendientes: number }>('POST', `/api/revision/${id}/resolver`, { decision }),
    descartar: (id: number) => request<{ pendientes: number }>('POST', `/api/revision/${id}/descartar`),
  },

  configuracion: {
    listar: () => request<ConfiguracionRespuesta>('GET', '/api/configuracion'),
    guardar: (key: string, valor: number | string) =>
      request<ConfiguracionRespuesta>('PUT', `/api/configuracion/${key}`, { valor }),
  },

  sync: {
    estado: () => request<EstadoSync>('GET', '/api/sync/estado'),
    lanzar: (conHistorial = false) =>
      request<{ lanzada: boolean }>('POST', `/api/sync${query({ con_historial: conHistorial })}`),
  },
}
