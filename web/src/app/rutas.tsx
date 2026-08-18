import { Navigate, Route, Routes } from 'react-router-dom'
import { Armazon } from './Armazon'
import { Guardia } from './Guardia'
import { Pagina } from './Pagina'
import { primeraRuta } from './secciones'
import { useSesion } from './sesion'
import { PantallaLogin } from '../features/login/PantallaLogin'
import { PantallaTablero } from '../features/tablero/PantallaTablero'
import { PantallaCalendario } from '../features/calendario/PantallaCalendario'
import { PantallaProveedores } from '../features/proveedores/PantallaProveedores'
import { PantallaProveedor } from '../features/proveedores/PantallaProveedor'
import { PantallaFacturas } from '../features/facturas/PantallaFacturas'
import { PantallaOrdenes } from '../features/ordenes/PantallaOrdenes'
import { PantallaVentas } from '../features/ventas/PantallaVentas'
import { PantallaProductos } from '../features/productos/PantallaProductos'
import { PantallaRevision } from '../features/revision/PantallaRevision'
import { PantallaMensajes } from '../features/mensajes/PantallaMensajes'
import { PantallaConfiguracion } from '../features/configuracion/PantallaConfiguracion'
import type { Seccion } from '../lib/types'
import type { ReactNode } from 'react'

function protegida(seccion: Seccion, pantalla: ReactNode) {
  return <Guardia seccion={seccion}>{pantalla}</Guardia>
}

function Inicio() {
  const { sesion } = useSesion()
  return <Navigate to={sesion ? primeraRuta(sesion.secciones) : '/entrar'} replace />
}

function NoEncontrada() {
  return (
    <Pagina titulo="Página no encontrada">
      <div className="aviso">Esa dirección no existe en el sistema.</div>
    </Pagina>
  )
}

export function Rutas() {
  return (
    <Routes>
      <Route path="/entrar" element={<PantallaLogin />} />
      <Route element={<Guardia><Armazon /></Guardia>}>
        <Route path="/" element={<Inicio />} />
        <Route path="/tablero" element={protegida('tablero', <PantallaTablero />)} />
        <Route path="/calendario" element={protegida('calendario', <PantallaCalendario />)} />
        <Route path="/revision" element={protegida('revision', <PantallaRevision />)} />
        <Route path="/facturas" element={protegida('facturas', <PantallaFacturas />)} />
        <Route path="/proveedores" element={protegida('proveedores', <PantallaProveedores />)} />
        <Route path="/proveedores/:slug" element={protegida('proveedores', <PantallaProveedor />)} />
        <Route path="/ordenes" element={protegida('ordenes', <PantallaOrdenes />)} />
        <Route path="/mensajes" element={protegida('mensajes', <PantallaMensajes />)} />
        <Route path="/ventas" element={protegida('ventas', <PantallaVentas />)} />
        <Route path="/productos" element={protegida('productos', <PantallaProductos />)} />
        <Route path="/configuracion" element={protegida('configuracion', <PantallaConfiguracion />)} />
        <Route path="*" element={<NoEncontrada />} />
      </Route>
    </Routes>
  )
}
