import { Link } from 'react-router-dom'
import { fecha, numero, pesos } from '../../lib/format'
import { Chapa } from '../../ui/Chapa'
import { TablaCaja } from '../../ui/Tabla'
import { Vacio } from '../../ui/Estado'
import type { Orden } from '../../lib/types'

interface Props {
  ordenes: Orden[]
  limiteDias: number
  alto?: number
  vacio: string
}

export function TablaOrdenes({ ordenes, limiteDias, alto, vacio }: Props) {
  if (!ordenes.length) return <Vacio>{vacio}</Vacio>

  return (
    <TablaCaja alto={alto}>
      <table className="tabla">
        <thead>
          <tr>
            <th>Orden</th>
            <th>Proveedor</th>
            <th>Producto</th>
            <th>Pedida</th>
            <th className="num">Cantidad</th>
            <th className="num">Estimado</th>
            <th>Estado</th>
            <th className="num">Antigüedad</th>
          </tr>
        </thead>
        <tbody>
          {ordenes.map((orden) => {
            const vieja = orden.age_days >= limiteDias && orden.status !== 'recibida'
            return (
              <tr key={orden.id}>
                <td className="fuerte">{orden.number}</td>
                <td>
                  {orden.supplier_slug
                    ? <Link to={`/proveedores/${orden.supplier_slug}`}>{orden.supplier_name}</Link>
                    : orden.supplier_name ?? '-'}
                </td>
                <td>{orden.product_description ?? orden.product_code ?? <span className="tenue">sin producto</span>}</td>
                <td className="num">{fecha(orden.ordered_on)}</td>
                <td className="num">{numero(orden.quantity)}</td>
                <td className="num fuerte">{pesos(orden.estimated_cents)}</td>
                <td>
                  <Chapa tono={orden.status === 'recibida' ? 'saldada' : 'neutra'}>{orden.status_raw}</Chapa>
                </td>
                <td className={vieja ? 'num rojo fuerte' : 'num tenue'}>{numero(orden.age_days)} d</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </TablaCaja>
  )
}
