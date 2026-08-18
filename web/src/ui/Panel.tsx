import type { ReactNode } from 'react'

interface Props {
  titulo: ReactNode
  nota?: ReactNode
  acciones?: ReactNode
  children: ReactNode
  /** Drop the body padding when the panel holds a table edge to edge. */
  pegado?: boolean
  alerta?: boolean
  className?: string
}

export function Panel({ titulo, nota, acciones, children, pegado, alerta, className }: Props) {
  return (
    <section className={['panel', alerta ? 'alerta' : '', className ?? ''].filter(Boolean).join(' ')}>
      <header className="panel-cabecera">
        <div className="fila" style={{ gap: 10 }}>
          <h2 className="panel-titulo">{titulo}</h2>
          {nota ? <span className="panel-nota">{nota}</span> : null}
        </div>
        {acciones ? <div className="fila">{acciones}</div> : null}
      </header>
      <div className={pegado ? 'panel-cuerpo pegado' : 'panel-cuerpo'}>{children}</div>
    </section>
  )
}
