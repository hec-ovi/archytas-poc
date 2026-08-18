import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useSesion } from './sesion'
import { Pagina } from './Pagina'
import type { Seccion } from '../lib/types'

/** No session, no app. A role without the section never even sees its link. */
export function Guardia({ seccion, children }: { seccion?: Seccion; children: ReactNode }) {
  const { sesion, verificando, puede } = useSesion()
  const lugar = useLocation()

  if (verificando) return <div className="cargando" style={{ paddingTop: 80 }}>Verificando la sesión</div>
  if (!sesion) return <Navigate to="/entrar" replace state={{ desde: lugar.pathname }} />
  if (seccion && !puede(seccion)) {
    return (
      <Pagina titulo="Sin acceso">
        <div className="aviso error">
          Tu usuario ({sesion.nombre}) no tiene acceso a esta sección. Pedile al dueño que te la habilite.
        </div>
      </Pagina>
    )
  }
  return <>{children}</>
}
