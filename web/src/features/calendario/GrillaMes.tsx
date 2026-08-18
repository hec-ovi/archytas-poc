import { useMemo } from 'react'
import { armarGrilla, DIAS_SEMANA, type Mes } from './mes'
import { CeldaDia } from './CeldaDia'
import type { EventoCalendario } from '../../lib/types'

interface Props {
  mes: Mes
  eventos: EventoCalendario[]
  diaElegido: string | null
  diaEncima: string | null
  arrastrado: number | null
  onElegirDia: (fecha: string) => void
  onAbrirEvento: (evento: EventoCalendario) => void
  onArrastrar: (id: number) => void
  onSoltarChip: () => void
  onEntrar: (fecha: string | null) => void
  onSoltarEnDia: (fecha: string, id: number) => void
}

export function GrillaMes(props: Props) {
  const casillas = useMemo(() => armarGrilla(props.mes), [props.mes])

  const porDia = useMemo(() => {
    const mapa = new Map<string, EventoCalendario[]>()
    for (const evento of props.eventos) {
      const grupo = mapa.get(evento.on_date) ?? []
      grupo.push(evento)
      mapa.set(evento.on_date, grupo)
    }
    for (const grupo of mapa.values()) {
      grupo.sort((a, b) => (b.balance_cents ?? b.amount_cents ?? 0) - (a.balance_cents ?? a.amount_cents ?? 0))
    }
    return mapa
  }, [props.eventos])

  return (
    <div className="cal-grilla">
      {DIAS_SEMANA.map((dia) => (
        <div key={dia} className="cal-cabecera">{dia}</div>
      ))}
      {casillas.map((casilla) => (
        <CeldaDia
          key={casilla.fecha}
          casilla={casilla}
          eventos={porDia.get(casilla.fecha) ?? []}
          elegido={props.diaElegido === casilla.fecha}
          encima={props.diaEncima === casilla.fecha}
          arrastrado={props.arrastrado}
          onElegir={props.onElegirDia}
          onAbrirEvento={props.onAbrirEvento}
          onArrastrar={props.onArrastrar}
          onSoltarChip={props.onSoltarChip}
          onEntrar={props.onEntrar}
          onSoltarEnDia={props.onSoltarEnDia}
        />
      ))}
    </div>
  )
}
