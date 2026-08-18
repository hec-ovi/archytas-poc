import type { ReactNode } from 'react'
import { Pulso } from './Pulso'

interface Props {
  titulo: string
  subtitulo?: ReactNode
  acciones?: ReactNode
  children: ReactNode
}

export function Pagina({ titulo, subtitulo, acciones, children }: Props) {
  return (
    <>
      <header className="encabezado">
        <div>
          <h1 className="titulo-pagina">{titulo}</h1>
          {subtitulo ? <div className="subtitulo-pagina">{subtitulo}</div> : null}
        </div>
        <div className="encabezado-acciones">
          {acciones}
          <Pulso />
        </div>
      </header>
      <div className="contenido">{children}</div>
    </>
  )
}
