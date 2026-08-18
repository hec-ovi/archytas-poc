import type { ReactNode } from 'react'
import type { EstadoPago } from '../lib/types'

type Tono = 'impaga' | 'parcial' | 'saldada' | 'neutra' | 'acento' | 'violeta'

export function Chapa({ tono = 'neutra', children }: { tono?: Tono; children: ReactNode }) {
  return <span className={`chapa ${tono}`}>{children}</span>
}

const TEXTO_ESTADO: Record<EstadoPago, string> = {
  impaga: 'Impaga',
  parcial: 'Pago parcial',
  saldada: 'Saldada',
}

export function ChapaEstado({ estado }: { estado: EstadoPago | null | undefined }) {
  if (!estado) return <Chapa>sin estado</Chapa>
  return <Chapa tono={estado}>{TEXTO_ESTADO[estado] ?? estado}</Chapa>
}

/** The mark the client asked for: an invoice whose receipt was never issued. */
export function MarcaSinRecibo({ tieneRecibo }: { tieneRecibo: number | boolean | null | undefined }) {
  if (tieneRecibo) return null
  return <span className="sin-recibo">sin recibo</span>
}
