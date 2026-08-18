import { pesos, numero } from '../../lib/format'
import { ESTADO_COLOR } from './paleta'

export interface TramoProporcion {
  clave: string
  texto: string
  cantidad: number
  centavos?: number
}

/** One row that shows how a total splits, with every slice named. Never colour alone. */
export function BarraProporcion({ tramos }: { tramos: TramoProporcion[] }) {
  const total = tramos.reduce((suma, tramo) => suma + tramo.cantidad, 0)
  return (
    <div className="pila" style={{ gap: 8 }}>
      <div style={{ display: 'flex', height: 12, gap: 2, background: 'var(--linea-suave)' }}>
        {tramos.map((tramo) => (
          <span
            key={tramo.clave}
            title={`${tramo.texto}: ${numero(tramo.cantidad)}`}
            style={{
              width: total ? `${(tramo.cantidad / total) * 100}%` : '0%',
              background: ESTADO_COLOR[tramo.clave] ?? 'var(--acento)',
            }}
          />
        ))}
      </div>
      <ul className="fila" style={{ gap: 14 }}>
        {tramos.map((tramo) => (
          <li key={tramo.clave} className="fila" style={{ gap: 6 }}>
            <span style={{ width: 9, height: 9, background: ESTADO_COLOR[tramo.clave] ?? 'var(--acento)' }} />
            <span>{tramo.texto}</span>
            <span className="num fuerte">{numero(tramo.cantidad)}</span>
            {tramo.centavos === undefined ? null : <span className="num tenue">{pesos(tramo.centavos)}</span>}
          </li>
        ))}
      </ul>
    </div>
  )
}
