import { fecha, pesos } from '../../lib/format'
import { Boton } from '../../ui/Boton'
import { Chapa, ChapaEstado, MarcaSinRecibo } from '../../ui/Chapa'
import { Panel } from '../../ui/Panel'
import { Vacio } from '../../ui/Estado'
import type { EventoCalendario } from '../../lib/types'

interface Props {
  dia: string
  eventos: EventoCalendario[]
  onAbrirEvento: (evento: EventoCalendario) => void
  onBorrar: (evento: EventoCalendario) => void
  onAgregar: () => void
}

/** What falls due on the day the person clicked. */
export function PanelDia({ dia, eventos, onAbrirEvento, onBorrar, onAgregar }: Props) {
  const total = eventos.reduce((suma, evento) => suma + (evento.balance_cents ?? evento.amount_cents ?? 0), 0)

  return (
    <Panel
      titulo={fecha(dia)}
      nota={eventos.length ? `${eventos.length} vencimientos · ${pesos(total)}` : 'sin vencimientos'}
      acciones={<Boton chico onClick={onAgregar}>Agregar acá</Boton>}
      pegado
    >
      {eventos.length === 0 ? (
        <Vacio>Ese día no vence nada.</Vacio>
      ) : (
        <ul className="lista-simple">
          {eventos.map((evento) => (
            <li key={evento.id}>
              <div className="fila" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ minWidth: 0 }}>
                  <div className="fuerte">{evento.supplier_name ?? evento.title}</div>
                  <div className="tenue" style={{ fontSize: 11.5 }}>
                    {evento.invoice_number ? `Factura ${evento.invoice_number}` : evento.title}
                    {evento.note ? ` · ${evento.note}` : ''}
                  </div>
                  <div className="fila" style={{ gap: 6, marginTop: 4 }}>
                    {evento.kind === 'vencimiento' ? (
                      <>
                        <ChapaEstado estado={evento.payment_state} />
                        <MarcaSinRecibo tieneRecibo={evento.has_receipt} />
                      </>
                    ) : (
                      <Chapa tono="acento">agregado a mano</Chapa>
                    )}
                    {evento.moved_from ? (
                      <span className="tenue" style={{ fontSize: 11 }}>movido desde {fecha(evento.moved_from)}</span>
                    ) : null}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="num fuerte">{pesos(evento.balance_cents ?? evento.amount_cents)}</div>
                  <div className="fila" style={{ justifyContent: 'flex-end', marginTop: 4 }}>
                    {evento.invoice_id ? (
                      <Boton chico variante="plano" onClick={() => onAbrirEvento(evento)}>Abrir factura</Boton>
                    ) : (
                      <Boton chico variante="peligro" onClick={() => onBorrar(evento)}>Borrar</Boton>
                    )}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  )
}
