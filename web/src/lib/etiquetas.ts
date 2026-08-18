// Names the api's short codes get on screen, shared by the screens that show the same thing.

export const ESTADO_VENTA: Record<string, string> = {
  valida: 'Suman al total',
  conflicto: 'En conflicto',
  rota: 'Datos rotos',
  duplicada: 'Duplicadas',
}

export const ESTADO_ORDEN: Record<string, string> = {
  'por-enviar': 'Por enviar',
  enviada: 'Enviada',
  confirmada: 'Confirmada',
  recibida: 'Recibida',
}

export const TIPO_MENSAJE: Record<string, string> = {
  reclamo: 'Reclamos',
  vencimiento: 'Vencimientos',
  stock: 'Stock',
}

export const TIPO_REVISION: Record<string, string> = {
  'venta-duplicada': 'Ventas duplicadas',
  'venta-rota': 'Ventas rotas',
  proveedor: 'Proveedores',
  rubro: 'Rubros',
}
