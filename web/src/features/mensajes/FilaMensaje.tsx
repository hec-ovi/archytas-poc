import { fecha } from '../../lib/format'
import { Boton } from '../../ui/Boton'
import { Chapa } from '../../ui/Chapa'
import type { Mensaje } from '../../lib/types'

const TIPO: Record<string, string> = {
  reclamo: 'Reclamo',
  vencimiento: 'Vencimiento',
  stock: 'Stock',
}

interface Props {
  mensaje: Mensaje
  trabajando: boolean
  onResolver: () => void
  onAbrirFactura: (id: number) => void
}

export function FilaMensaje({ mensaje, trabajando, onResolver, onAbrirFactura }: Props) {
  return (
    <li className={mensaje.resolved ? 'msj resuelto' : 'msj'}>
      <div>
        <div className="fuerte">{mensaje.supplier_name ?? mensaje.sender}</div>
        <div className="tenue" style={{ fontSize: 11.5 }}>{fecha(mensaje.received_on)}</div>
        <div style={{ marginTop: 4 }}>
          <Chapa tono={mensaje.kind === 'reclamo' ? 'impaga' : mensaje.kind === 'vencimiento' ? 'parcial' : 'neutra'}>
            {TIPO[mensaje.kind] ?? mensaje.kind}
          </Chapa>
        </div>
      </div>

      <div style={{ minWidth: 0 }}>
        <div className="fuerte">{mensaje.subject}</div>
        <div className="msj-cuerpo">{mensaje.body}</div>
      </div>

      <div className="msj-acciones">
        {mensaje.resolved ? (
          <>
            <Chapa tono="saldada">resuelto</Chapa>
            <span className="tenue" style={{ fontSize: 11.5 }}>
              por {mensaje.resolved_by ?? '-'}
            </span>
          </>
        ) : (
          <Boton chico variante="principal" disabled={trabajando} onClick={onResolver}>
            {trabajando ? 'Cerrando…' : 'Marcar resuelto'}
          </Boton>
        )}
        {mensaje.invoice_id && mensaje.invoice_number ? (
          <Boton chico variante="plano" onClick={() => onAbrirFactura(mensaje.invoice_id as number)}>
            Ver factura {mensaje.invoice_number}
          </Boton>
        ) : null}
      </div>
    </li>
  )
}
