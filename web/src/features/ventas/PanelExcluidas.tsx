import { useMemo, useState } from 'react'
import { fecha, numero, pesos } from '../../lib/format'
import { Chapa } from '../../ui/Chapa'
import { Panel } from '../../ui/Panel'
import { Campo } from '../../ui/Campo'
import { TablaCaja } from '../../ui/Tabla'
import { Vacio } from '../../ui/Estado'
import { ESTADO_VENTA } from '../../lib/etiquetas'
import type { VentaExcluida } from '../../lib/types'

/** The client asked to be told which sales are broken instead of having them summed. */
export function PanelExcluidas({ excluidas }: { excluidas: VentaExcluida[] }) {
  const [motivo, setMotivo] = useState('')

  const tipos = useMemo(
    () => Array.from(new Set(excluidas.map((venta) => venta.status))),
    [excluidas],
  )
  const filas = motivo ? excluidas.filter((venta) => venta.status === motivo) : excluidas
  const total = filas.reduce((suma, venta) => suma + (venta.total_cents ?? 0), 0)

  return (
    <Panel
      titulo="Ventas que quedaron fuera del total"
      nota={`${filas.length} filas · ${pesos(total)} sin sumar`}
      acciones={
        <Campo etiqueta="">
          <select value={motivo} onChange={(evento) => setMotivo(evento.target.value)}>
            <option value="">Todos los motivos</option>
            {tipos.map((tipo) => (
              <option key={tipo} value={tipo}>
                {ESTADO_VENTA[tipo] ?? tipo} ({excluidas.filter((v) => v.status === tipo).length})
              </option>
            ))}
          </select>
        </Campo>
      }
      alerta
      pegado
    >
      {filas.length === 0 ? (
        <Vacio>Todas las ventas cargadas suman al total.</Vacio>
      ) : (
        <TablaCaja alto={420}>
          <table className="tabla">
            <thead>
              <tr>
                <th>Venta</th>
                <th>Fecha</th>
                <th>Cliente</th>
                <th>Producto</th>
                <th className="num">Cantidad</th>
                <th className="num">Unitario</th>
                <th className="num">Total</th>
                <th>Motivo</th>
                <th className="ancho">Qué pasa</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((venta) => (
                <tr key={venta.id}>
                  <td className="fuerte mono">{venta.code}</td>
                  <td className="num">{venta.sold_on ? fecha(venta.sold_on) : <span className="rojo">sin fecha</span>}</td>
                  <td>{venta.customer ?? '-'}</td>
                  <td>{venta.product_description ?? venta.product_code ?? <span className="tenue">sin producto</span>}</td>
                  <td className="num">{numero(venta.quantity)}</td>
                  <td className="num">{pesos(venta.unit_cents)}</td>
                  <td className="num">{pesos(venta.total_cents)}</td>
                  <td>
                    <Chapa tono={venta.status === 'rota' ? 'impaga' : 'parcial'}>
                      {ESTADO_VENTA[venta.status] ?? venta.status}
                    </Chapa>
                  </td>
                  <td className="ancho">{venta.status_note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TablaCaja>
      )}
    </Panel>
  )
}
