import { atraso, fecha, pesos } from '../../lib/format'
import { ChapaEstado, MarcaSinRecibo } from '../../ui/Chapa'
import { TablaCaja } from '../../ui/Tabla'
import { Vacio } from '../../ui/Estado'
import type { Factura } from '../../lib/types'

interface Props {
  facturas: Factura[]
  onAbrir: (id: number) => void
  vacio: string
  limite?: number
}

/** The compact invoice list the dashboard panels share. */
export function TablaVencimientos({ facturas, onAbrir, vacio, limite = 12 }: Props) {
  if (!facturas.length) return <Vacio>{vacio}</Vacio>
  const visibles = facturas.slice(0, limite)

  return (
    <TablaCaja>
      <table className="tabla">
        <thead>
          <tr>
            <th>Factura</th>
            <th>Proveedor</th>
            <th>Vence</th>
            <th className="num">Saldo</th>
            <th>Estado</th>
            <th className="num">Atraso</th>
          </tr>
        </thead>
        <tbody>
          {visibles.map((factura) => (
            <tr key={factura.id} className="clickeable" onClick={() => onAbrir(factura.id)}>
              <td className="fuerte">{factura.number}</td>
              <td>{factura.supplier_name}</td>
              <td className="num">{fecha(factura.due_on)}</td>
              <td className="num fuerte">{pesos(factura.balance_cents)}</td>
              <td>
                <div className="fila" style={{ gap: 6 }}>
                  <ChapaEstado estado={factura.payment_state} />
                  <MarcaSinRecibo tieneRecibo={factura.has_receipt} />
                </div>
              </td>
              <td className={factura.days_overdue > 0 ? 'num rojo' : 'num tenue'}>{atraso(factura.days_overdue)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TablaCaja>
  )
}
