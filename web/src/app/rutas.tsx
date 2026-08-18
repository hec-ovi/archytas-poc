import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Armazon } from './Armazon'
import { Guardia } from './Guardia'
import { Pagina } from './Pagina'
import { primeraRuta } from './secciones'
import { useSesion } from './sesion'
import { PantallaLogin } from '../features/login/PantallaLogin'

// each screen ships on its own, so opening the calendar does not download the charts
const PantallaTablero = lazy(() => import('../features/tablero/PantallaTablero').then((m) => ({ default: m.PantallaTablero })))
const PantallaCalendario = lazy(() => import('../features/calendario/PantallaCalendario').then((m) => ({ default: m.PantallaCalendario })))
const PantallaProveedores = lazy(() => import('../features/proveedores/PantallaProveedores').then((m) => ({ default: m.PantallaProveedores })))
const PantallaProveedor = lazy(() => import('../features/proveedores/PantallaProveedor').then((m) => ({ default: m.PantallaProveedor })))
const PantallaFacturas = lazy(() => import('../features/facturas/PantallaFacturas').then((m) => ({ default: m.PantallaFacturas })))
const PantallaOrdenes = lazy(() => import('../features/ordenes/PantallaOrdenes').then((m) => ({ default: m.PantallaOrdenes })))
const PantallaVentas = lazy(() => import('../features/ventas/PantallaVentas').then((m) => ({ default: m.PantallaVentas })))
const PantallaProductos = lazy(() => import('../features/productos/PantallaProductos').then((m) => ({ default: m.PantallaProductos })))
const PantallaRevision = lazy(() => import('../features/revision/PantallaRevision').then((m) => ({ default: m.PantallaRevision })))
const PantallaMensajes = lazy(() => import('../features/mensajes/PantallaMensajes').then((m) => ({ default: m.PantallaMensajes })))
const PantallaConfiguracion = lazy(() => import('../features/configuracion/PantallaConfiguracion').then((m) => ({ default: m.PantallaConfiguracion })))
import type { Seccion } from '../lib/types'
import type { ReactNode } from 'react'

function protegida(seccion: Seccion, pantalla: ReactNode) {
  return (
    <Guardia seccion={seccion}>
      <Suspense fallback={<div className="cargando" style={{ paddingTop: 60 }}>Abriendo la sección</div>}>
        {pantalla}
      </Suspense>
    </Guardia>
  )
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
