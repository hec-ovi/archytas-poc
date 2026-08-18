// How each setting is shown and written. Cents never reach the person: the form talks pesos.

export interface Presentacion {
  titulo: string
  ayuda: string
  unidad: string
  enPesos?: boolean
  minimo?: number
}

export const PRESENTACION: Record<string, Presentacion> = {
  sync_horas: {
    titulo: 'Cada cuánto se actualiza desde el portal',
    ayuda: 'El portal viejo publica dos veces por día. Con 12 horas alcanza.',
    unidad: 'horas',
    minimo: 1,
  },
  aviso_dias_antes: {
    titulo: 'Cuántos días antes avisar de un vencimiento',
    ayuda: 'Con cuánta anticipación querés enterarte de que una factura vence.',
    unidad: 'días',
    minimo: 0,
  },
  aviso_monto_minimo: {
    titulo: 'Monto mínimo para avisar',
    ayuda: 'Debajo de este monto no se manda aviso, para no llenar el teléfono.',
    unidad: 'pesos',
    enPesos: true,
    minimo: 0,
  },
  orden_vieja_dias: {
    titulo: 'Cuándo una orden se considera olvidada',
    ayuda: 'Días que puede estar abierta una orden de compra antes de aparecer como olvidada.',
    unidad: 'días',
    minimo: 1,
  },
  recibo_dias_antes: {
    titulo: 'Cuántos días antes reclamar el recibo',
    ayuda: 'Antes del vencimiento, para llegar a emitirlo a tiempo.',
    unidad: 'días',
    minimo: 0,
  },
}

export function aFormulario(key: string, valor: number | string): string {
  const presentacion = PRESENTACION[key]
  if (presentacion?.enPesos) return String(Math.round(Number(valor) / 100))
  return String(valor)
}

export function aGuardar(key: string, texto: string): number | null {
  const numero = Number(texto.replace(',', '.'))
  if (!Number.isFinite(numero)) return null
  const presentacion = PRESENTACION[key]
  return presentacion?.enPesos ? Math.round(numero * 100) : Math.round(numero)
}
