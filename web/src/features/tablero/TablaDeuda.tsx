import { Link } from 'react-router-dom'
import { diasTexto, pesos } from '../../lib/format'
import { Barrita } from '../../ui/Barrita'
import { TablaCaja } from '../../ui/Tabla'
import type { PosicionProveedor } from '../../lib/types'

export function TablaDeuda({ proveedores }: { proveedores: PosicionProveedor[] }) {
  const mayor = Math.max(1, ...proveedores.map((p) => p.owed_cents))

  return (
    <TablaCaja alto={320}>
      <table className="tabla">
        <thead>
          <tr>
            <th>Proveedor</th>
            <th className="num">Comprado</th>
            <th className="num">Pagado</th>
            <th className="num">Debemos</th>
            <th style={{ width: 120 }}>Peso</th>
            <th className="num">Más atrasada</th>
          </tr>
        </thead>
        <tbody>
          {proveedores.map((proveedor) => (
            <tr key={proveedor.supplier_id}>
              <td><Link to={`/proveedores/${proveedor.slug}`}>{proveedor.name}</Link></td>
              <td className="num tenue">{pesos(proveedor.purchased_cents)}</td>
              <td className="num tenue">{pesos(proveedor.paid_cents)}</td>
              <td className="num fuerte">{pesos(proveedor.owed_cents)}</td>
              <td><Barrita parte={proveedor.owed_cents} total={mayor} tono="rojo" /></td>
              <td className="num">
                {proveedor.oldest_overdue_days && proveedor.oldest_overdue_days > 0
                  ? <span className="rojo">{diasTexto(proveedor.oldest_overdue_days)}</span>
                  : <span className="tenue">al día</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TablaCaja>
  )
}
