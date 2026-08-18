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
export function TablaVencimientos({ facturas, onAbrir, vacio, limite = 10 }: Props) {
  if (!facturas.length) return <Vacio>{vacio}</Vacio>
  const visibles = facturas.slice(0, limite)

  return (
    <>
      <TablaCaja>
        <table className="tabla">
          <thead>
            <tr>
              <th>Factura</th>
              <th>Proveedor</th>
              <th className="num">Vence</th>
              <th className="num">Saldo</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {visibles.map((factura) => (
              <tr key={factura.id} className="clickeable" onClick={() => onAbrir(factura.id)}>
                <td className="fuerte">{factura.number}</td>
                <td>{factura.supplier_name}</td>
                <td className="num">
                  {fecha(factura.due_on)}
                  <div className={factura.days_overdue > 0 ? 'rojo' : 'tenue'} style={{ fontSize: 11 }}>
                    {atraso(factura.days_overdue)}
                  </div>
                </td>
                <td className="num fuerte">{pesos(factura.balance_cents)}</td>
                <td>
                  <div className="fila" style={{ gap: 6, flexWrap: 'nowrap' }}>
                    <ChapaEstado estado={factura.payment_state} />
                    <MarcaSinRecibo tieneRecibo={factura.has_receipt} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TablaCaja>
      {facturas.length > limite ? (
        <div className="tenue" style={{ padding: '6px 10px', fontSize: 11.5 }}>
          Se muestran {limite} de {facturas.length}.
        </div>
      ) : null}
    </>
  )
}
