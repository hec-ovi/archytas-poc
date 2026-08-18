import { pesos } from '../../lib/format'
import type { EventoCalendario } from '../../lib/types'

interface Props {
  evento: EventoCalendario
  onAbrir: (evento: EventoCalendario) => void
  onArrastrar: (id: number) => void
  onSoltar: () => void
  arrastrando: boolean
}

const SUFIJOS = /\s+(S\.?A\.?|S\.?R\.?L\.?|SAS|SACIF)\.?$/i

/** Chips are narrow: the legal suffix is the first thing that can go. */
function nombreCorto(nombre: string): string {
  return nombre.replace(SUFIJOS, '')
}

export function claseEstado(evento: EventoCalendario): string {
  if (evento.kind !== 'vencimiento') return 'recordatorio'
  return evento.payment_state ?? 'impaga'
}

/** One due date on the grid: who, how much, how it is paid, and whether the receipt is missing. */
export function ChipEvento({ evento, onAbrir, onArrastrar, onSoltar, arrastrando }: Props) {
  const monto = evento.balance_cents ?? evento.amount_cents
  const sinRecibo = evento.kind === 'vencimiento' && !evento.has_receipt

  return (
    <button
      className={['cal-chip', claseEstado(evento), arrastrando ? 'arrastrando' : ''].filter(Boolean).join(' ')}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('text/plain', String(evento.id))
        onArrastrar(evento.id)
      }}
      onDragEnd={onSoltar}
      onClick={(e) => {
        e.stopPropagation()
        onAbrir(evento)
      }}
      title={`${evento.supplier_name ?? evento.title}. Arrastralo a otro día para mover el vencimiento.`}
    >
      <span className="proveedor">{nombreCorto(evento.supplier_name ?? evento.title)}</span>
      <span className="monto">
        <span>{pesos(monto)}</span>
        {sinRecibo ? <span className="marca-recibo" title="Todavía sin recibo emitido" /> : null}
      </span>
    </button>
  )
}
