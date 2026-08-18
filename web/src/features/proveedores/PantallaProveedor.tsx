import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../lib/api'
import { useRecurso } from '../../lib/useRecurso'
import { useEventoVivo } from '../../lib/useCanalVivo'
import { fecha, numero, pesos } from '../../lib/format'
import { Pagina } from '../../app/Pagina'
import { Panel } from '../../ui/Panel'
import { Metrica } from '../../ui/Metrica'
import { Bloque, Vacio } from '../../ui/Estado'
import { Pestanias } from '../../ui/Pestanias'
import { Chapa } from '../../ui/Chapa'
import { TablaCaja } from '../../ui/Tabla'
import { TablaFacturas } from '../facturas/TablaFacturas'
import { ModalFactura } from '../facturas/ModalFactura'
import { PanelAlias } from './PanelAlias'
import { leerCumplimiento } from './cumplimiento'

type Solapa = 'facturas' | 'pagos' | 'ordenes' | 'mensajes'

export function PantallaProveedor() {
  const { slug = '' } = useParams()
  const recurso = useRecurso(() => api.proveedores.detalle(slug), [slug])
  const listado = useRecurso(() => api.proveedores.listar(), [])
  const [solapa, setSolapa] = useState<Solapa>('facturas')
  const [factura, setFactura] = useState<number | null>(null)

  useEventoVivo('factura-actualizada', () => recurso.recargar())
  useEventoVivo('recibo-emitido', () => recurso.recargar())

  const cumplimiento = useMemo(() => {
    const fila = listado.datos?.cumplimiento.find((c) => c.supplier_id === recurso.datos?.proveedor.id)
    return leerCumplimiento(fila)
  }, [listado.datos, recurso.datos])

  return (
    <Pagina
      titulo={recurso.datos?.proveedor.name ?? 'Proveedor'}
      subtitulo={<Link to="/proveedores">‹ Volver a todos los proveedores</Link>}
    >
      <Bloque recurso={recurso} que="Cargando el proveedor">
        {(datos) => (
          <div className="pila">
            <div className="grilla g4">
              <Metrica rotulo="Comprado" valor={pesos(datos.posicion?.purchased_cents ?? 0)} pie={`${numero(datos.facturas.length)} facturas`} />
              <Metrica rotulo="Pagado" valor={pesos(datos.posicion?.paid_cents ?? 0)} pie={`${numero(datos.pagos.length)} pagos`} />
              <Metrica rotulo="Debemos" valor={pesos(datos.posicion?.owed_cents ?? 0)} tono="urgente"
                pie={(datos.posicion?.oldest_overdue_days ?? 0) > 0
                  ? `la más vieja lleva ${numero(datos.posicion?.oldest_overdue_days ?? 0)} días`
                  : 'al día'} />
              <Metrica
                rotulo="Cumplimiento del plazo"
                valor={cumplimiento.porcentaje === null ? '-' : `${cumplimiento.porcentaje}%`}
                pie={`plazo acordado ${datos.proveedor.terms_days ?? '-'} días · ${cumplimiento.texto}`}
                tono={cumplimiento.tono === 'verde' ? 'calma' : cumplimiento.tono === 'rojo' ? 'urgente' : 'aviso'}
              />
            </div>

            <div className="grilla g-2-1">
              <Panel titulo="Datos de contacto">
                <dl className="definiciones">
                  <dt>CUIT</dt><dd className="mono">{datos.proveedor.cuit ?? '-'}</dd>
                  <dt>Mail</dt>
                  <dd>{datos.proveedor.email ? <a href={`mailto:${datos.proveedor.email}`}>{datos.proveedor.email}</a> : '-'}</dd>
                  <dt>Teléfono</dt><dd>{datos.proveedor.phone ?? '-'}</dd>
                  <dt>Dirección</dt><dd>{datos.proveedor.address ?? '-'}</dd>
                  <dt>Plazo de pago</dt>
                  <dd>
                    {datos.proveedor.terms_days ? `${datos.proveedor.terms_days} días` : 'sin plazo cargado'}
                    {datos.proveedor.terms_raw ? <span className="tenue"> (llegó como “{datos.proveedor.terms_raw}”)</span> : null}
                  </dd>
                  <dt>Ficha</dt>
                  <dd>{datos.proveedor.confirmed ? <Chapa tono="saldada">confirmada</Chapa> : <Chapa tono="parcial">a confirmar</Chapa>}</dd>
                </dl>
              </Panel>

              <PanelAlias proveedor={datos.proveedor} alias={datos.alias} />
            </div>

            <Panel titulo="Movimientos" pegado>
              <Pestanias
                activa={solapa}
                onCambiar={setSolapa}
                opciones={[
                  { clave: 'facturas', texto: 'Facturas', cuenta: datos.facturas.length },
                  { clave: 'pagos', texto: 'Pagos', cuenta: datos.pagos.length },
                  { clave: 'ordenes', texto: 'Órdenes', cuenta: datos.ordenes.length },
                  { clave: 'mensajes', texto: 'Mensajes', cuenta: datos.mensajes.length },
                ]}
              />

              {solapa === 'facturas' ? (
                <TablaFacturas facturas={datos.facturas} onAbrir={setFactura} conProveedor={false} alto={420} />
              ) : null}

              {solapa === 'pagos' ? (
                datos.pagos.length ? (
                  <TablaCaja alto={420}>
                    <table className="tabla">
                      <thead>
                        <tr><th>Fecha</th><th>Factura</th><th>Referencia</th><th>Cargado por</th><th className="num">Monto</th></tr>
                      </thead>
                      <tbody>
                        {datos.pagos.map((pago) => (
                          <tr key={pago.id}>
                            <td className="num">{fecha(pago.paid_on)}</td>
                            <td className="fuerte">{pago.invoice_number ?? '-'}</td>
                            <td className="mono">{pago.reference ?? '-'}</td>
                            <td>{pago.created_by}</td>
                            <td className="num fuerte">{pesos(pago.amount_cents)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </TablaCaja>
                ) : <Vacio>No hay pagos registrados a este proveedor.</Vacio>
              ) : null}

              {solapa === 'ordenes' ? (
                datos.ordenes.length ? (
                  <TablaCaja alto={420}>
                    <table className="tabla">
                      <thead>
                        <tr><th>Orden</th><th>Producto</th><th>Pedida</th><th className="num">Cantidad</th><th className="num">Estimado</th><th>Estado</th><th className="num">Antigüedad</th></tr>
                      </thead>
                      <tbody>
                        {datos.ordenes.map((orden) => (
                          <tr key={orden.id}>
                            <td className="fuerte">{orden.number}</td>
                            <td>{orden.product_description ?? orden.product_code ?? '-'}</td>
                            <td className="num">{fecha(orden.ordered_on)}</td>
                            <td className="num">{numero(orden.quantity)}</td>
                            <td className="num">{pesos(orden.estimated_cents)}</td>
                            <td><Chapa>{orden.status_raw}</Chapa></td>
                            <td className="num">{numero(orden.age_days)} d</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </TablaCaja>
                ) : <Vacio>No hay órdenes de compra a este proveedor.</Vacio>
              ) : null}

              {solapa === 'mensajes' ? (
                datos.mensajes.length ? (
                  <ul className="lista-simple">
                    {datos.mensajes.map((mensaje) => (
                      <li key={mensaje.id}>
                        <div className="fila" style={{ justifyContent: 'space-between' }}>
                          <span className="fuerte">{mensaje.subject}</span>
                          <span className="fila" style={{ gap: 8 }}>
                            <Chapa tono={mensaje.resolved ? 'saldada' : 'parcial'}>
                              {mensaje.resolved ? 'resuelto' : 'abierto'}
                            </Chapa>
                            <span className="tenue">{fecha(mensaje.received_on)}</span>
                          </span>
                        </div>
                        <div className="medio" style={{ marginTop: 3 }}>{mensaje.body}</div>
                      </li>
                    ))}
                  </ul>
                ) : <Vacio>Este proveedor no mandó mensajes.</Vacio>
              ) : null}
            </Panel>
          </div>
        )}
      </Bloque>

      {factura === null ? null : (
        <ModalFactura id={factura} onCerrar={() => setFactura(null)} onCambio={recurso.recargar} />
      )}
    </Pagina>
  )
}
