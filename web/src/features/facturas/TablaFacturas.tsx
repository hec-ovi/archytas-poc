import { Link } from 'react-router-dom'
import { atraso, fecha, pesos } from '../../lib/format'
import { ChapaEstado, ChapaOrigen, MarcaSinRecibo } from '../../ui/Chapa'
import { TablaCaja, Th, ordenar, useOrden } from '../../ui/Tabla'
import { Vacio } from '../../ui/Estado'
import type { Factura } from '../../lib/types'

/** What each column sorts by. The api answers ordered by due date, so that is where it starts. */
const CLAVES: Record<string, (factura: Factura) => unknown> = {
  factura: (f) => f.number,
  proveedor: (f) => f.supplier_name,
  emitida: (f) => f.issued_on,
  vence: (f) => f.due_on,
  monto: (f) => f.amount_cents,
  pagado: (f) => f.paid_cents,
  saldo: (f) => f.balance_cents,
  estado: (f) => ESTADOS[f.payment_state] ?? 9,
  origen: (f) => f.source_kind,
  recibo: (f) => Boolean(f.has_receipt),
  atraso: (f) => f.days_overdue,
}

/** Payment state sorts by how much it needs attention, not alphabetically. */
const ESTADOS: Record<string, number> = { impaga: 0, parcial: 1, saldada: 2 }

/** Money, dates and lateness are asked about biggest first. */
const DESC_PRIMERO = ['monto', 'pagado', 'saldo', 'atraso', 'emitida']

interface Props {
  facturas: Factura[]
  onAbrir: (id: number) => void
  seleccionada?: number | null
  conProveedor?: boolean
  alto?: number
}

export function TablaFacturas({ facturas, onAbrir, seleccionada, conProveedor = true, alto }: Props) {
  const { orden, alternar } = useOrden({ columna: 'vence', direccion: 'asc' }, DESC_PRIMERO)

  if (!facturas.length) return <Vacio>No hay facturas que cumplan con el filtro.</Vacio>

  const ordenadas = ordenar(facturas, CLAVES[orden.columna] ?? CLAVES.vence, orden.direccion)
  const cabecera = { orden, onOrdenar: alternar }

  return (
    <TablaCaja alto={alto}>
      <table className="tabla">
        <thead>
          <tr>
            <Th columna="factura" {...cabecera}>Factura</Th>
            {conProveedor ? <Th columna="proveedor" {...cabecera}>Proveedor</Th> : null}
            <Th columna="emitida" {...cabecera}>Emitida</Th>
            <Th columna="vence" {...cabecera}>Vence</Th>
            <Th columna="monto" num {...cabecera}>Monto</Th>
            <Th columna="pagado" num {...cabecera}>Pagado</Th>
            <Th columna="saldo" num {...cabecera}>Saldo</Th>
            <Th columna="estado" {...cabecera}>Estado</Th>
            <Th columna="origen" {...cabecera}>Llegó como</Th>
            <Th columna="recibo" {...cabecera}>Recibo</Th>
            <Th columna="atraso" num {...cabecera}>Atraso</Th>
          </tr>
        </thead>
        <tbody>
          {ordenadas.map((factura) => (
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
              <td><ChapaOrigen origen={factura.source_kind} /></td>
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
