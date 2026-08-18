import type { ReactNode } from 'react'
import { Boton } from './Boton'

export function Cargando({ que = 'Cargando' }: { que?: string }) {
  return <div className="cargando">{que}</div>
}

export function AvisoError({ mensaje, reintentar }: { mensaje: string; reintentar?: () => void }) {
  return (
    <div className="aviso error" role="alert">
      <div>{mensaje}</div>
      {reintentar ? (
        <div style={{ marginTop: 8 }}>
          <Boton chico onClick={reintentar}>Reintentar</Boton>
        </div>
      ) : null}
    </div>
  )
}

export function Vacio({ children }: { children: ReactNode }) {
  return <div className="vacio">{children}</div>
}

interface BloqueProps<T> {
  recurso: { datos: T | null; cargando: boolean; error: string | null; recargar: () => void }
  que?: string
  children: (datos: T) => ReactNode
}

/** Loading, error and content in one place, so no screen can render blank without saying why. */
export function Bloque<T>({ recurso, que, children }: BloqueProps<T>) {
  if (recurso.error) return <AvisoError mensaje={recurso.error} reintentar={recurso.recargar} />
  if (!recurso.datos) return <Cargando que={que} />
  return <>{children(recurso.datos)}</>
}
