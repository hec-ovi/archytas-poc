import { BrowserRouter } from 'react-router-dom'
import { ProveedorSesion } from './app/sesion'
import { ProveedorCanal } from './lib/useCanalVivo'
import { Rutas } from './app/rutas'

export function App() {
  return (
    <BrowserRouter>
      <ProveedorSesion>
        <ProveedorCanal>
          <Rutas />
        </ProveedorCanal>
      </ProveedorSesion>
    </BrowserRouter>
  )
}
