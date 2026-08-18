import { useState } from 'react'
import { api } from '../../lib/api'
import { useRecurso } from '../../lib/useRecurso'
import { useEventoVivo } from '../../lib/useCanalVivo'
import { fechaHora, numero, pesos } from '../../lib/format'
import { ESTADO_VENTA } from '../../lib/etiquetas'
import { Pagina } from '../../app/Pagina'
import { useSesion } from '../../app/sesion'
import { Panel } from '../../ui/Panel'
import { Bloque } from '../../ui/Estado'
import { Boton } from '../../ui/Boton'
import { SerieMensual } from '../../ui/graficos/SerieMensual'
import { BarrasCategoria } from '../../ui/graficos/BarrasCategoria'
import { BarraProporcion } from '../../ui/graficos/BarraProporcion'
import { ModalFactura } from '../facturas/ModalFactura'
import { TarjetasAtencion } from './TarjetasAtencion'
import { TablaVencimientos } from './TablaVencimientos'
import { TablaDeuda } from './TablaDeuda'
import { TablaOrdenesOlvidadas } from './TablaOrdenesOlvidadas'

export function PantallaTablero() {
  const { puede } = useSesion()
  const recurso = useRecurso(() => api.tablero(), [])
  const [factura, setFactura] = useState<number | null>(null)
  const abrirFactura = (id: number) => { if (puede('facturas')) setFactura(id) }

  useEventoVivo('factura-actualizada', () => recurso.recargar())
  useEventoVivo('recibo-emitido', () => recurso.recargar())
  useEventoVivo('sincronizacion-lista', () => recurso.recargar())

  return (
    <Pagina
      titulo="Tablero"
      subtitulo="Primero lo que necesita atención. Los totales van más abajo."
      acciones={<Boton onClick={recurso.recargar} disabled={recurso.cargando}>
        {recurso.cargando ? 'Actualizando…' : 'Actualizar'}
      </Boton>}
    >
      <Bloque recurso={recurso} que="Cargando el tablero">
        {(datos) => (
          <div className="pila">
            <TarjetasAtencion datos={datos} />

            {puede('facturas') ? (
              <div className="grilla g2">
                <Panel
                  titulo="Vencen en los próximos días"
                  nota={`${datos.vencen_pronto.length} facturas`}
                  alerta
                  pegado
                >
                  <TablaVencimientos
                    facturas={datos.vencen_pronto}
                    onAbrir={abrirFactura}
                    vacio="No hay vencimientos inmediatos."
                  />
                </Panel>

                <Panel
                  titulo="Recibidas y sin recibo emitido"
                  nota={`${datos.sin_recibo.length} facturas`}
                  alerta
                  pegado
                >
                  <TablaVencimientos
                    facturas={datos.sin_recibo}
                    onAbrir={abrirFactura}
                    vacio="Todas las facturas tienen su comprobante."
                  />
                </Panel>
              </div>
            ) : null}

            <div className="grilla g-2-1">
              {puede('ordenes') ? (
                <Panel
                  titulo="Órdenes de compra olvidadas"
                  nota={`${datos.ordenes_olvidadas.length} abiertas hace demasiado`}
                  pegado
                >
                  <TablaOrdenesOlvidadas ordenes={datos.ordenes_olvidadas} />
                </Panel>
              ) : null}

              <Panel titulo="Qué se puede sumar y qué no" nota="antes de mirar cualquier total">
                <div className="pila" style={{ gap: 16 }}>
                  {puede('facturas') ? (
                    <div>
                      <div className="rotulo" style={{ marginBottom: 6 }}>Estado de las facturas</div>
                      <BarraProporcion
                        tramos={[
                          { clave: 'impaga', texto: 'Impagas', cantidad: datos.estado_pagos.impaga },
                          { clave: 'parcial', texto: 'Parciales', cantidad: datos.estado_pagos.parcial },
                          { clave: 'saldada', texto: 'Saldadas', cantidad: datos.estado_pagos.saldada },
                        ]}
                      />
                    </div>
                  ) : null}
                  <div>
                    <div className="rotulo" style={{ marginBottom: 6 }}>Ventas que no suman</div>
                    <BarraProporcion
                      tramos={[
                        {
                          clave: 'valida',
                          texto: 'Válidas',
                          cantidad: datos.salud_ventas.validas.count,
                          centavos: datos.salud_ventas.validas.cents,
                        },
                        ...Object.entries(datos.salud_ventas.excluidas).map(([clave, valor]) => ({
                          clave,
                          texto: ESTADO_VENTA[clave] ?? clave,
                          cantidad: valor.count,
                          centavos: valor.cents,
                        })),
                      ]}
                    />
                  </div>
                </div>
              </Panel>
            </div>

            {puede('proveedores') ? (
              <Panel
                titulo="Deuda por proveedor"
                nota="qué compramos, qué pagamos y qué queda"
                pegado
              >
                <TablaDeuda proveedores={datos.deuda_por_proveedor} />
              </Panel>
            ) : null}

            <div className="grilla g-2-1">
              <Panel titulo="Facturación por mes" nota="solo las ventas que se pueden sumar">
                <SerieMensual datos={datos.ventas_por_mes} alto={240} />
              </Panel>

              {puede('proveedores') ? (
                <Panel titulo="Compras por rubro" nota="lo facturado por proveedores">
                  <BarrasCategoria
                    tituloValor="Comprado"
                    datos={datos.gasto_por_rubro
                      .slice()
                      .sort((a, b) => b.purchased_cents - a.purchased_cents)
                      .map((rubro) => ({
                        etiqueta: rubro.category,
                        valor: rubro.purchased_cents,
                        nota: `${numero(rubro.product_count)} artículos`,
                      }))}
                  />
                </Panel>
              ) : null}
            </div>

            <Panel
              titulo="Última actualización desde el portal"
              nota={datos.ultima_sincronizacion ? fechaHora(datos.ultima_sincronizacion.finished_at) : 'nunca'}
            >
              {datos.ultima_sincronizacion ? (
                <div className="fila" style={{ gap: 24 }}>
                  <span>
                    Estado <strong>{datos.ultima_sincronizacion.status}</strong>
                  </span>
                  <span>
                    Registros guardados{' '}
                    <strong className="num">{numero(datos.ultima_sincronizacion.summary.guardados ?? 0)}</strong>
                  </span>
                  <span>
                    Mandados a revisión{' '}
                    <strong className="num">{numero(datos.ultima_sincronizacion.summary.a_revision ?? 0)}</strong>
                  </span>
                  <span className="tenue">Origen: {datos.ultima_sincronizacion.trigger}</span>
                </div>
              ) : (
                <div className="tenue">Todavía no se corrió ninguna actualización.</div>
              )}
            </Panel>

            {datos.productos_nuevos.length ? (
              <Panel titulo="Productos nuevos en el catálogo" nota={`${datos.productos_nuevos.length}`} pegado>
                <table className="tabla">
                  <thead>
                    <tr><th>Código</th><th>Descripción</th><th className="num">Precio</th><th className="num">Stock</th></tr>
                  </thead>
                  <tbody>
                    {datos.productos_nuevos.map((producto) => (
                      <tr key={producto.id}>
                        <td className="mono">{producto.code}</td>
                        <td>{producto.description}</td>
                        <td className="num">{pesos(producto.price_cents)}</td>
                        <td className="num">{numero(producto.stock)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Panel>
            ) : null}
          </div>
        )}
      </Bloque>

      {factura === null ? null : (
        <ModalFactura id={factura} onCerrar={() => setFactura(null)} onCambio={recurso.recargar} />
      )}
    </Pagina>
  )
}
