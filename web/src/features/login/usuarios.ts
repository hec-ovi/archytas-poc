// The three people who use the system, as the login screen offers them.

export interface UsuarioDemo {
  usuario: string
  nombre: string
  detalle: string
}

export const USUARIOS: UsuarioDemo[] = [
  { usuario: 'duenio', nombre: 'Dueño', detalle: 'Ve todo el sistema' },
  { usuario: 'marcela', nombre: 'Marcela', detalle: 'Compras, facturas y calendario' },
  { usuario: 'julian', nombre: 'Julián', detalle: 'Ventas y productos' },
]
