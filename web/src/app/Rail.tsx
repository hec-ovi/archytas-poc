import { NavLink } from 'react-router-dom'
import { MENU } from './secciones'
import { useSesion } from './sesion'
import { useContadores } from './contadores'
import type { Seccion } from '../lib/types'

const ROL_TEXTO: Record<string, string> = {
  duenio: 'Dirección',
  compras: 'Compras',
  ventas: 'Ventas',
}

export function Rail() {
  const { sesion, salir, puede } = useSesion()
  const { revision, mensajes } = useContadores()

  const insignia = (seccion: Seccion): number | null => {
    if (seccion === 'revision') return revision && revision > 0 ? revision : null
    if (seccion === 'mensajes') return mensajes && mensajes > 0 ? mensajes : null
    return null
  }

  return (
    <nav className="rail">
      <div className="rail-marca">
        <strong>Cordillera</strong>
        <span>Ferretería Industrial</span>
      </div>

      <ul className="rail-nav">
        {MENU.filter((item) => puede(item.seccion)).map((item) => {
          const cuenta = insignia(item.seccion)
          return (
            <li key={item.seccion}>
              <NavLink
                to={item.ruta}
                className={({ isActive }) => (isActive ? 'rail-link activo' : 'rail-link')}
              >
                <span>{item.texto}</span>
                {cuenta === null ? null : <span className="rail-pastilla">{cuenta}</span>}
              </NavLink>
            </li>
          )
        })}
      </ul>

      <div className="rail-pie">
        <div className="usuario">{sesion?.nombre}</div>
        <div className="rol">{ROL_TEXTO[sesion?.rol ?? ''] ?? sesion?.rol}</div>
        <button className="rail-salir" onClick={() => void salir()}>Salir</button>
      </div>
    </nav>
  )
}
