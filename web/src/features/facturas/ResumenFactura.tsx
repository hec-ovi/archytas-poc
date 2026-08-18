import { Link } from 'react-router-dom'
import { atraso, fecha, pesos } from '../../lib/format'
import { Barrita } from '../../ui/Barrita'
import { ChapaEstado, MarcaSinRecibo } from '../../ui/Chapa'
import type { Factura } from '../../lib/types'

export function ResumenFactura({ factura }: { factura: Factura }) {
  return (
    <div className="grilla g2">
      <dl className="definiciones">
        <dt>Proveedor</dt>
        <dd>
          {factura.supplier_slug
            ? <Link to={`/proveedores/${factura.supplier_slug}`}>{factura.supplier_name}</Link>
            : factura.supplier_name ?? '-'}
        </dd>
        <dt>Emitida</dt>
        <dd>{fecha(factura.issued_on)}</dd>
        <dt>Vence</dt>
        <dd>
          {fecha(factura.due_on)}{' '}
          <span className={factura.days_overdue > 0 && factura.payment_state !== 'saldada' ? 'rojo' : 'tenue'}>
            ({atraso(factura.days_overdue)})
          </span>
        </dd>
        {factura.terms_days ? (
          <>
            <dt>Plazo acordado</dt>
            <dd>{factura.terms_days} días</dd>
          </>
        ) : null}
        <dt>Mail</dt>
        <dd>{factura.supplier_email ?? '-'}</dd>
      </dl>

      <div className="pila" style={{ gap: 8 }}>
        <div className="fila" style={{ justifyContent: 'space-between' }}>
          <span className="rotulo">Monto</span>
          <span className="num fuerte" style={{ fontSize: 16 }}>{pesos(factura.amount_cents)}</span>
        </div>
        <div className="fila" style={{ justifyContent: 'space-between' }}>
          <span className="rotulo">Pagado</span>
          <span className="num">{pesos(factura.paid_cents)}</span>
        </div>
        <div className="fila" style={{ justifyContent: 'space-between' }}>
          <span className="rotulo">Saldo</span>
          <span className="num fuerte">{pesos(factura.balance_cents)}</span>
        </div>
        <Barrita
          parte={factura.paid_cents}
          total={factura.amount_cents}
          tono={factura.payment_state === 'saldada' ? 'verde' : factura.payment_state === 'parcial' ? 'ambar' : 'rojo'}
        />
        <div className="fila" style={{ gap: 10, marginTop: 4 }}>
          <ChapaEstado estado={factura.payment_state} />
          <MarcaSinRecibo tieneRecibo={factura.has_receipt} />
        </div>
      </div>
    </div>
  )
}
