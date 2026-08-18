import type { Cumplimiento } from '../../lib/types'

export interface Nota {
  porcentaje: number | null
  texto: string
  tono: 'verde' | 'ambar' | 'rojo' | 'tenue'
}

/** How often this supplier's invoices were paid inside the agreed term. */
export function leerCumplimiento(fila: Cumplimiento | undefined): Nota {
  if (!fila || !fila.invoice_count) return { porcentaje: null, texto: 'sin facturas', tono: 'tenue' }
  const valor = Math.round((fila.on_terms_count / fila.invoice_count) * 100)
  return {
    porcentaje: valor,
    texto: `${valor}% (${fila.on_terms_count} de ${fila.invoice_count})`,
    tono: valor >= 80 ? 'verde' : valor >= 50 ? 'ambar' : 'rojo',
  }
}
