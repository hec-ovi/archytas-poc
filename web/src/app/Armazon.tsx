import { Outlet } from 'react-router-dom'
import { Rail } from './Rail'
import { ProveedorContadores } from './contadores'

export function Armazon() {
  return (
    <ProveedorContadores>
      <div className="armazon">
        <Rail />
        <main className="columna">
          <Outlet />
        </main>
      </div>
    </ProveedorContadores>
  )
}
