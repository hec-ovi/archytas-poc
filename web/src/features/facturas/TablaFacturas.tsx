import { Link } from 'react-router-dom'
import { atraso, fecha, pesos } from '../../lib/format'
import { ChapaEstado, MarcaSinRecibo } from '../../ui/Chapa'
import { TablaCaja } from '../../ui/Tabla'
import { Vacio } from '../../ui/Estado'
import type { Factura } from '../../lib/types'

interface Props {
  facturas: Factura[]
  onAbrir: (id: number) => void
  seleccionada?: number | null
  conProveedor?: boolean
  alto?: number
}

export function TablaFacturas({ facturas, onAbrir, seleccionada, conProveedor = true, alto }: Props) {
  if (!facturas.length) return <Vacio>No hay facturas que cumplan con el filtro.</Vacio>

  return (
    <TablaCaja alto={alto}>
      <table className="tabla">
        <thead>
          <tr>
            <th>Factura</th>
            {conProveedor ? <th>Proveedor</th> : null}
            <th>Emitida</th>
            <th>Vence</th>
            <th className="num">Monto</th>
            <th className="num">Pagado</th>
            <th className="num">Saldo</th>
            <th>Estado</th>
            <th>Recibo</th>
            <th className="num">Atraso</th>
          </tr>
        </thead>
        <tbody>
          {facturas.map((factura) => (
            <tr
              key={factura.id}
              className={factura.id === seleccionada ? 'clickeable seleccionada' : 'clickeable'}
              onClick={() => onAbrir(factura.id)}
            >
              <td className="fuerte">{factura.number}</td>
              {conProveedor ? (
                <td>
                  {factura.supplier_slug ? (
                    <Link to={`/proveedores/${factura.supplier_slug}`} onClick={(e) => e.stopPropagation()}>
                      {factura.supplier_name}
                    </Link>
                  ) : (
                    factura.supplier_name ?? <span className="tenue">sin proveedor</span>
                  )}
                </td>
              ) : null}
              <td className="num">{fecha(factura.issued_on)}</td>
              <td className="num">{fecha(factura.due_on)}</td>
              <td className="num">{pesos(factura.amount_cents)}</td>
              <td className="num tenue">{pesos(factura.paid_cents)}</td>
              <td className="num fuerte">{pesos(factura.balance_cents)}</td>
              <td><ChapaEstado estado={factura.payment_state} /></td>
              <td>{factura.has_receipt ? <span className="tenue">emitido</span> : <MarcaSinRecibo tieneRecibo={0} />}</td>
              <td className={factura.days_overdue > 0 && factura.payment_state !== 'saldada' ? 'num rojo' : 'num tenue'}>
                {atraso(factura.days_overdue)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TablaCaja>
  )
}
