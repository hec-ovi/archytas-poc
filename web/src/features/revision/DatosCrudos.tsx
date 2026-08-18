import { pesos } from '../../lib/format'

interface Campo {
  clave: string
  etiqueta: string
  centavos?: boolean
}

// the order a person reads them in, not the order the api happens to send
const CAMPOS: Campo[] = [
  { clave: 'codigo', etiqueta: 'Código' },
  { clave: 'customer', etiqueta: 'Cliente' },
  { clave: 'cliente', etiqueta: 'Cliente' },
  { clave: 'proveedor', etiqueta: 'Proveedor' },
  { clave: 'categoria', etiqueta: 'Rubro' },
  { clave: 'date_raw', etiqueta: 'Fecha como llegó' },
  { clave: 'fecha', etiqueta: 'Fecha' },
  { clave: 'sold_on', etiqueta: 'Fecha entendida' },
  { clave: 'product_raw', etiqueta: 'Producto como llegó' },
  { clave: 'productoId', etiqueta: 'Producto como llegó' },
  { clave: 'quantity', etiqueta: 'Cantidad' },
  { clave: 'cantidad', etiqueta: 'Cantidad' },
  { clave: 'unit_cents', etiqueta: 'Precio unitario', centavos: true },
  { clave: 'total_cents', etiqueta: 'Total', centavos: true },
  { clave: 'repairs', etiqueta: 'Arreglos automáticos' },
]

const OCULTOS = new Set(['filas', 'product_id'])

function texto(valor: unknown, centavos?: boolean): string {
  if (valor === null || valor === undefined || valor === '') return '(vacío)'
  if (Array.isArray(valor)) return valor.length ? valor.join('; ') : '(ninguno)'
  if (centavos && typeof valor === 'number') return pesos(valor)
  if (typeof valor === 'object') return JSON.stringify(valor)
  return String(valor)
}

/** What actually arrived, field by field, with nothing hidden. */
export function DatosCrudos({ datos }: { datos: Record<string, unknown> }) {
  const conocidos = CAMPOS.filter((campo) => campo.clave in datos)
  const restantes: Campo[] = Object.keys(datos)
    .filter((clave) => !OCULTOS.has(clave) && !CAMPOS.some((campo) => campo.clave === clave))
    .map((clave) => ({ clave, etiqueta: clave }))
  const filas = [...conocidos, ...restantes]
    .filter((campo) => !(campo.clave === 'repairs' && !(datos.repairs as unknown[])?.length))

  if (!filas.length) return null

  return (
    <dl className="definiciones dos-columnas">
      {filas.map((campo) => {
        const valor = datos[campo.clave]
        const vacio = valor === null || valor === undefined || valor === ''
        return (
          <div key={campo.clave} style={{ display: 'contents' }}>
            <dt>{campo.etiqueta}</dt>
            <dd className={vacio ? 'rojo' : ''}>{texto(valor, campo.centavos)}</dd>
          </div>
        )
      })}
    </dl>
  )
}
