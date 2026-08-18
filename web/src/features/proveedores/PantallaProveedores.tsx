import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../lib/api'
import { useRecurso } from '../../lib/useRecurso'
import { diasTexto, numero, pesos } from '../../lib/format'
import { Pagina } from '../../app/Pagina'
import { Panel } from '../../ui/Panel'
import { Metrica } from '../../ui/Metrica'
import { Barrita } from '../../ui/Barrita'
import { Bloque } from '../../ui/Estado'
import { Campo } from '../../ui/Campo'
import { TablaCaja } from '../../ui/Tabla'
import { leerCumplimiento } from './cumplimiento'

export function PantallaProveedores() {
  const recurso = useRecurso(() => api.proveedores.listar(), [])
  const [busqueda, setBusqueda] = useState('')

  const cumplimientoPorId = useMemo(() => {
    const mapa = new Map<number, ReturnType<typeof leerCumplimiento>>()
    for (const fila of recurso.datos?.cumplimiento ?? []) mapa.set(fila.supplier_id, leerCumplimiento(fila))
    return mapa
  }, [recurso.datos])

  const filas = useMemo(() => {
    const texto = busqueda.trim().toLowerCase()
    return (recurso.datos?.proveedores ?? [])
      .filter((p) => !texto || `${p.name} ${p.cuit ?? ''} ${p.email ?? ''}`.toLowerCase().includes(texto))
      .sort((a, b) => b.owed_cents - a.owed_cents)
  }, [recurso.datos, busqueda])

  const totales = useMemo(() => ({
    comprado: filas.reduce((s, p) => s + p.purchased_cents, 0),
    pagado: filas.reduce((s, p) => s + p.paid_cents, 0),
    debemos: filas.reduce((s, p) => s + p.owed_cents, 0),
    atrasados: filas.filter((p) => (p.oldest_overdue_days ?? 0) > 0).length,
  }), [filas])

  const mayorDeuda = Math.max(1, ...filas.map((p) => p.owed_cents))

  return (
    <Pagina
      titulo="Proveedores"
      subtitulo="Qué le compramos a cada uno, qué le pagamos y qué le debemos hoy."
    >
      <Bloque recurso={recurso} que="Cargando los proveedores">
        {(datos) => (
          <div className="pila">
            <div className="grilla g4">
              <Metrica rotulo="Proveedores" valor={numero(datos.proveedores.length)} pie="con movimientos cargados" />
              <Metrica rotulo="Comprado" valor={pesos(totales.comprado)} pie="histórico facturado" />
              <Metrica rotulo="Pagado" valor={pesos(totales.pagado)} pie="registrado en el sistema" />
              <Metrica rotulo="Debemos" valor={pesos(totales.debemos)} pie={`${totales.atrasados} con facturas vencidas`} tono="urgente" />
            </div>

            <Panel
              titulo="Posición de cada proveedor"
              nota="ordenados por lo que les debemos"
              acciones={
                <Campo etiqueta="" className="crecer">
                  <input
                    value={busqueda}
                    onChange={(evento) => setBusqueda(evento.target.value)}
                    placeholder="Buscar por nombre, CUIT o mail"
                    style={{ minWidth: 240 }}
                  />
                </Campo>
              }
              pegado
            >
              <TablaCaja alto={520}>
                <table className="tabla">
                  <thead>
                    <tr>
                      <th>Proveedor</th>
                      <th>CUIT</th>
                      <th className="num">Plazo</th>
                      <th className="num">Facturas</th>
                      <th className="num">Comprado</th>
                      <th className="num">Pagado</th>
                      <th className="num">Debemos</th>
                      <th style={{ width: 110 }}>Peso</th>
                      <th className="num">Más atrasada</th>
                      <th className="num">Cumplimiento</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filas.map((proveedor) => {
                      const nota = cumplimientoPorId.get(proveedor.supplier_id)
                      return (
                        <tr key={proveedor.supplier_id}>
                          <td className="fuerte">
                            <Link to={`/proveedores/${proveedor.slug}`}>{proveedor.name}</Link>
                          </td>
                          <td className="mono">{proveedor.cuit ?? '-'}</td>
                          <td className="num">{proveedor.terms_days ? `${proveedor.terms_days} d` : '-'}</td>
                          <td className="num">{numero(proveedor.invoice_count)}</td>
                          <td className="num tenue">{pesos(proveedor.purchased_cents)}</td>
                          <td className="num tenue">{pesos(proveedor.paid_cents)}</td>
                          <td className="num fuerte">{pesos(proveedor.owed_cents)}</td>
                          <td><Barrita parte={proveedor.owed_cents} total={mayorDeuda} tono="rojo" /></td>
                          <td className="num">
                            {(proveedor.oldest_overdue_days ?? 0) > 0
                              ? <span className="rojo">{diasTexto(proveedor.oldest_overdue_days)}</span>
                              : <span className="tenue">al día</span>}
                          </td>
                          <td className={`num ${nota?.tono ?? 'tenue'}`}>{nota?.texto ?? '-'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </TablaCaja>
            </Panel>
          </div>
        )}
      </Bloque>
    </Pagina>
  )
}
