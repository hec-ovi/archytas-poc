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

const ORIGEN: Record<string, { texto: string; ayuda: string }> = {
  pdf: { texto: 'PDF', ayuda: 'Llegó como PDF con texto: se lee derecho.' },
  'pdf-escaneado': { texto: 'PDF escaneado', ayuda: 'Llegó escaneado: es una foto del papel, se leyó con OCR.' },
  excel: { texto: 'Excel', ayuda: 'Llegó como planilla de Excel.' },
  portal: { texto: 'Portal', ayuda: 'Se leyó directo del portal, sin archivo adjunto.' },
}

/** What format the supplier actually sent, so nobody opens a scan expecting a spreadsheet. */
export function ChapaOrigen({ origen }: { origen: string | null | undefined }) {
  if (!origen) return null
  const dato = ORIGEN[origen]
  return (
    <span className="chapa neutra" title={dato?.ayuda}>
      {dato?.texto ?? origen}
    </span>
  )
}
