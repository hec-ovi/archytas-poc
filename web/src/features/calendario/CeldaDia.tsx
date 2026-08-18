import { pesosCorto } from '../../lib/format'
import { ChipEvento } from './ChipEvento'
import type { Casilla } from './mes'
import type { EventoCalendario } from '../../lib/types'

interface Props {
  casilla: Casilla
  eventos: EventoCalendario[]
  elegido: boolean
  encima: boolean
  arrastrado: number | null
  onElegir: (fecha: string) => void
  onAbrirEvento: (evento: EventoCalendario) => void
  onArrastrar: (id: number) => void
  onSoltarChip: () => void
  onEntrar: (fecha: string | null) => void
  onSoltarEnDia: (fecha: string, id: number) => void
}

const MAXIMO_VISIBLE = 3

export function CeldaDia(props: Props) {
  const { casilla, eventos, elegido, encima, arrastrado } = props
  const total = eventos.reduce((suma, evento) => suma + (evento.balance_cents ?? evento.amount_cents ?? 0), 0)

  const clases = [
    'cal-dia',
    casilla.delMes ? '' : 'afuera',
    casilla.finDeSemana ? 'finde' : '',
    casilla.esHoy ? 'hoy' : '',
    elegido ? 'elegido' : '',
    encima ? 'encima' : '',
  ].filter(Boolean).join(' ')

  return (
    <div
      className={clases}
      onClick={() => props.onElegir(casilla.fecha)}
      onDragOver={(e) => {
        e.preventDefault()
        e.dataTransfer.dropEffect = 'move'
        props.onEntrar(casilla.fecha)
      }}
      onDragLeave={() => props.onEntrar(null)}
      onDrop={(e) => {
        e.preventDefault()
        props.onEntrar(null)
        // the id travels in the drag payload, not in state, so the drop never guesses
        const id = Number(e.dataTransfer.getData('text/plain'))
        if (Number.isFinite(id) && id > 0) props.onSoltarEnDia(casilla.fecha, id)
      }}
    >
      <div className="cal-tope">
        <span className="cal-numero">{casilla.dia}</span>
        {total > 0 ? <span className="cal-total">{pesosCorto(total)}</span> : null}
      </div>

      {eventos.slice(0, MAXIMO_VISIBLE).map((evento) => (
        <ChipEvento
          key={evento.id}
          evento={evento}
          onAbrir={props.onAbrirEvento}
          onArrastrar={props.onArrastrar}
          onSoltar={props.onSoltarChip}
          arrastrando={arrastrado === evento.id}
        />
      ))}

      {eventos.length > MAXIMO_VISIBLE ? (
        <span className="cal-mas">+{eventos.length - MAXIMO_VISIBLE} más</span>
      ) : null}
    </div>
  )
}
