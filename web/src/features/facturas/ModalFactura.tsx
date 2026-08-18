import { useState } from 'react'
import { api } from '../../lib/api'
import { useRecurso } from '../../lib/useRecurso'
import { fecha, pesos } from '../../lib/format'
import { Bloque } from '../../ui/Estado'
import { Modal } from '../../ui/Modal'
import { Pestanias } from '../../ui/Pestanias'
import { Vacio } from '../../ui/Estado'
import { ResumenFactura } from './ResumenFactura'
import { FormularioPago } from './FormularioPago'
import { FormularioAjuste } from './FormularioAjuste'
import { AccionRecibo } from './AccionRecibo'

type Solapa = 'detalle' | 'pago' | 'recibo' | 'ajuste'

interface Props {
  id: number
  onCerrar: () => void
  /** Fired after any action, so the list behind the modal can refresh. */
  onCambio?: () => void
}

export function ModalFactura({ id, onCerrar, onCambio }: Props) {
  const [solapa, setSolapa] = useState<Solapa>('detalle')
  const recurso = useRecurso(() => api.facturas.detalle(id), [id])

  const refrescar = () => {
    recurso.recargar()
    onCambio?.()
  }

  return (
    <Modal
      titulo={<><strong>Factura {recurso.datos?.factura.number ?? ''}</strong>
        <span className="tenue">{recurso.datos?.factura.supplier_name ?? ''}</span></>}
      onCerrar={onCerrar}
      ancho
    >
      <Bloque recurso={recurso} que="Cargando la factura">
        {(datos) => (
          <div className="pila">
            <ResumenFactura factura={datos.factura} />

            <Pestanias
              activa={solapa}
              onCambiar={setSolapa}
              opciones={[
                { clave: 'detalle', texto: 'Pagos', cuenta: datos.pagos.length },
                { clave: 'pago', texto: 'Registrar pago' },
                { clave: 'recibo', texto: 'Recibo' },
                { clave: 'ajuste', texto: 'Ajustar monto' },
              ]}
            />

            {solapa === 'detalle' ? (
              datos.pagos.length ? (
                <table className="tabla">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Referencia</th>
                      <th>Cargado por</th>
                      <th className="num">Monto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datos.pagos.map((pago) => (
                      <tr key={pago.id}>
                        <td className="num">{fecha(pago.paid_on)}</td>
                        <td className="mono">{pago.reference ?? '-'}</td>
                        <td>{pago.created_by}</td>
                        <td className="num fuerte">{pesos(pago.amount_cents)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colSpan={3}>Total pagado</td>
                      <td className="num">{pesos(datos.factura.paid_cents)}</td>
                    </tr>
                  </tfoot>
                </table>
              ) : (
                <Vacio>Todavía no se registró ningún pago de esta factura.</Vacio>
              )
            ) : null}

            {solapa === 'pago' ? <FormularioPago factura={datos.factura} onListo={refrescar} /> : null}
            {solapa === 'recibo' ? <AccionRecibo factura={datos.factura} recibo={datos.recibo} onListo={refrescar} /> : null}
            {solapa === 'ajuste' ? (
              <FormularioAjuste
                factura={datos.factura}
                ajustes={datos.cruda.extra?.ajustes ?? []}
                onListo={refrescar}
              />
            ) : null}
          </div>
        )}
      </Bloque>
    </Modal>
  )
}
