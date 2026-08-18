import type { ReactNode } from 'react'

/** The one tooltip shape every chart uses. */
export function TooltipCaja({ titulo, filas }: { titulo: ReactNode; filas: { texto: string; valor: string }[] }) {
  return (
    <div className="tooltip">
      <div className="clave">{titulo}</div>
      {filas.map((fila) => (
        <div key={fila.texto} className="fila" style={{ justifyContent: 'space-between', gap: 14 }}>
          <span className="tenue">{fila.texto}</span>
          <span className="num fuerte">{fila.valor}</span>
        </div>
      ))}
    </div>
  )
}
