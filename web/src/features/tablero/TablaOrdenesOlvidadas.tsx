import { fecha, numero, pesos } from '../../lib/format'
import { Chapa } from '../../ui/Chapa'
import { TablaCaja } from '../../ui/Tabla'
import { Vacio } from '../../ui/Estado'
import type { Orden } from '../../lib/types'

export function TablaOrdenesOlvidadas({ ordenes, limite = 10 }: { ordenes: Orden[]; limite?: number }) {
  if (!ordenes.length) return <Vacio>No hay órdenes olvidadas.</Vacio>

  return (
    <TablaCaja>
      <table className="tabla">
        <thead>
          <tr>
            <th>Orden</th>
            <th>Proveedor</th>
            <th>Pedida</th>
            <th className="num">Antigüedad</th>
            <th className="num">Estimado</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {ordenes.slice(0, limite).map((orden) => (
            <tr key={orden.id}>
              <td className="fuerte">{orden.number}</td>
              <td>{orden.supplier_name}</td>
              <td className="num">{fecha(orden.ordered_on)}</td>
              <td className="num rojo">{numero(orden.age_days)} d</td>
              <td className="num">{pesos(orden.estimated_cents)}</td>
              <td><Chapa>{orden.status_raw}</Chapa></td>
            </tr>
          ))}
        </tbody>
      </table>
    </TablaCaja>
  )
}
