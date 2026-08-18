const ETIQUETAS: Record<string, string> = {
  customer: 'Cliente',
  cliente: 'Cliente',
  date_raw: 'Fecha como llegó',
  fecha: 'Fecha',
  sold_on: 'Fecha entendida',
  product_id: 'Producto',
  product_raw: 'Producto como llegó',
  productoId: 'Producto como llegó',
  quantity: 'Cantidad',
  cantidad: 'Cantidad',
  unit_cents: 'Precio unitario (centavos)',
  precioUnit: 'Precio unitario',
  total_cents: 'Total (centavos)',
  total: 'Total',
  codigo: 'Código',
  repairs: 'Arreglos automáticos',
  proveedor: 'Proveedor',
  categoria: 'Rubro',
}

function texto(valor: unknown): string {
  if (valor === null || valor === undefined || valor === '') return '(vacío)'
  if (Array.isArray(valor)) return valor.length ? valor.join('; ') : '(ninguno)'
  if (typeof valor === 'object') return JSON.stringify(valor)
  return String(valor)
}

/** What actually arrived, field by field, with nothing hidden. */
export function DatosCrudos({ datos }: { datos: Record<string, unknown> }) {
  const entradas = Object.entries(datos).filter(([clave]) => clave !== 'filas')
  if (!entradas.length) return null

  return (
    <dl className="definiciones">
      {entradas.map(([clave, valor]) => (
        <div key={clave} style={{ display: 'contents' }}>
          <dt>{ETIQUETAS[clave] ?? clave}</dt>
          <dd className={valor === '' || valor === null ? 'rojo' : ''}>{texto(valor)}</dd>
        </div>
      ))}
    </dl>
  )
}
