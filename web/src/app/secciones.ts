// The menu, in the order it reads best. A role only ever sees the sections it has.

import type { Seccion } from '../lib/types'

export interface EntradaMenu {
  seccion: Seccion
  ruta: string
  texto: string
}

export const MENU: EntradaMenu[] = [
  { seccion: 'tablero', ruta: '/tablero', texto: 'Tablero' },
  { seccion: 'calendario', ruta: '/calendario', texto: 'Calendario' },
  { seccion: 'revision', ruta: '/revision', texto: 'Revisión' },
  { seccion: 'facturas', ruta: '/facturas', texto: 'Facturas' },
  { seccion: 'proveedores', ruta: '/proveedores', texto: 'Proveedores' },
  { seccion: 'ordenes', ruta: '/ordenes', texto: 'Órdenes de compra' },
  { seccion: 'mensajes', ruta: '/mensajes', texto: 'Mensajes' },
  { seccion: 'ventas', ruta: '/ventas', texto: 'Ventas' },
  { seccion: 'productos', ruta: '/productos', texto: 'Productos' },
  { seccion: 'configuracion', ruta: '/configuracion', texto: 'Configuración' },
]

/** Where a person lands after logging in: the first section their role actually has. */
export function primeraRuta(secciones: Seccion[]): string {
  const entrada = MENU.find((item) => secciones.includes(item.seccion))
  return entrada?.ruta ?? '/sin-secciones'
}
