// Turning a click on a candidate into the payload `/api/revision/{id}/resolver` expects.

import { numero, pesos } from '../../lib/format'
import type { CandidatoRevision, PendienteRevision, VentaExcluida } from '../../lib/types'

/** The portal sends amounts in whole pesos inside a raw row; the rest of the app talks cents. */
export function textoCandidato(candidato: CandidatoRevision): string {
  if (candidato.fila) {
    const cantidad = candidato.fila.cantidad
    const total = Number(candidato.fila.total)
    if (cantidad && Number.isFinite(total)) {
      return `${numero(Number(cantidad))} unidades por ${pesos(total * 100)}`
    }
  }
  if (typeof candidato.valor === 'number') return pesos(candidato.valor)
  return String(candidato.valor)
}

/** The raw row of a duplicate carries no hash, so it is matched against the stored sale. */
export function huellaDeFila(
  fila: Record<string, string> | undefined,
  excluidas: VentaExcluida[] | null,
): string | null {
  if (!fila || !excluidas) return null
  const clave = firma(fila)
  const encontrada = excluidas.find((venta) => venta.extra?.crudo && firma(venta.extra.crudo) === clave)
  return encontrada?.row_hash ?? null
}

function firma(fila: Record<string, string>): string {
  return Object.keys(fila).sort().map((clave) => `${clave}=${String(fila[clave]).trim()}`).join('|')
}

export interface Eleccion {
  decision: Record<string, unknown>
  /** False when the choice cannot be applied yet and would only be recorded. */
  aplica: boolean
}

export function armarDecision(
  pendiente: PendienteRevision,
  candidato: CandidatoRevision,
  excluidas: VentaExcluida[] | null,
): Eleccion {
  if (pendiente.kind === 'venta-duplicada') {
    const huella = huellaDeFila(candidato.fila, excluidas)
    if (!huella) return { decision: { fila: candidato.fila, elegido: candidato.valor }, aplica: false }
    return { decision: { codigo_valido: true, row_hash: huella, elegido: candidato.valor }, aplica: true }
  }

  if (pendiente.kind === 'proveedor') {
    return { decision: { proveedor_slug: String(candidato.valor) }, aplica: true }
  }

  if (pendiente.kind === 'rubro') {
    return { decision: { rubro_slug: String(candidato.valor) }, aplica: true }
  }

  return { decision: { valor_elegido: candidato.valor, nota: candidato.nota ?? '' }, aplica: true }
}
