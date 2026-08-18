import { useState, type ReactNode } from 'react'

/** Wide tables scroll inside this box, never the page. */
export function TablaCaja({ children, alto }: { children: ReactNode; alto?: number }) {
  return (
    <div className="tabla-caja" style={alto ? { maxHeight: alto } : undefined}>
      {children}
    </div>
  )
}

export type Direccion = 'asc' | 'desc'

export interface Orden {
  columna: string
  direccion: Direccion
}

/**
 * Sorting state for a table.
 *
 * Clicking the column already sorted flips the direction; clicking another one starts it
 * ascending, except for amounts and dates, where what a person wants first is almost always
 * the biggest or the most recent.
 */
export function useOrden(inicial: Orden, descPrimero: string[] = []) {
  const [orden, setOrden] = useState<Orden>(inicial)

  const alternar = (columna: string) => {
    setOrden((actual) =>
      actual.columna === columna
        ? { columna, direccion: actual.direccion === 'asc' ? 'desc' : 'asc' }
        : { columna, direccion: descPrimero.includes(columna) ? 'desc' : 'asc' },
    )
  }

  return { orden, alternar }
}

/**
 * Sorts rows by whatever the accessor returns.
 *
 * Empty values always land at the bottom, in both directions: a row with no due date is not
 * "the earliest" nor "the latest", it is just missing, and burying it is what a person
 * expects. ISO dates compare as text, which is already chronological.
 */
export function ordenar<T>(filas: T[], valor: (fila: T) => unknown, direccion: Direccion): T[] {
  const signo = direccion === 'asc' ? 1 : -1
  return [...filas].sort((izquierda, derecha) => {
    const a = valor(izquierda)
    const b = valor(derecha)
    const vacioA = a === null || a === undefined || a === ''
    const vacioB = b === null || b === undefined || b === ''
    if (vacioA || vacioB) return vacioA && vacioB ? 0 : vacioA ? 1 : -1
    if (typeof a === 'number' && typeof b === 'number') return (a - b) * signo
    if (typeof a === 'boolean' && typeof b === 'boolean') return (Number(a) - Number(b)) * signo
    return String(a).localeCompare(String(b), 'es', { numeric: true }) * signo
  })
}

interface ThProps {
  children: ReactNode
  /** Naming a column makes the header sortable. Without it, it is a plain header. */
  columna?: string
  orden?: Orden
  onOrdenar?: (columna: string) => void
  num?: boolean
}

export function Th({ children, columna, orden, onOrdenar, num }: ThProps) {
  const clases = [num ? 'num' : '', columna ? 'ordenable' : ''].filter(Boolean).join(' ')

  if (!columna || !onOrdenar) {
    return <th className={clases || undefined}>{children}</th>
  }

  const activa = orden?.columna === columna
  const flecha = activa ? (orden!.direccion === 'asc' ? '▲' : '▼') : '↕'

  return (
    <th className={[clases, activa ? 'ordenando' : ''].filter(Boolean).join(' ')} aria-sort={
      activa ? (orden!.direccion === 'asc' ? 'ascending' : 'descending') : 'none'
    }>
      <button type="button" className="th-boton" onClick={() => onOrdenar(columna)} title="Ordenar por esta columna">
        <span>{children}</span>
        <span className="th-flecha">{flecha}</span>
      </button>
    </th>
  )
}
