import { useMemo, useState } from 'react'
import { api } from '../../lib/api'
import { useRecurso } from '../../lib/useRecurso'
import { useEventoVivo } from '../../lib/useCanalVivo'
import { fecha, numero, pesos } from '../../lib/format'
import { Pagina } from '../../app/Pagina'
import { Panel } from '../../ui/Panel'
import { Metrica } from '../../ui/Metrica'
import { Campo } from '../../ui/Campo'
import { Chapa } from '../../ui/Chapa'
import { Bloque, Vacio } from '../../ui/Estado'
import { TablaCaja } from '../../ui/Tabla'
import { ModalPrecios } from './ModalPrecios'

const STOCK_BAJO = 10

export function PantallaProductos() {
  const recurso = useRecurso(() => api.productos.listar(), [])
  const [rubro, setRubro] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [elegido, setElegido] = useState<number | null>(null)

  useEventoVivo('sincronizacion-lista', () => recurso.recargar())

  const rubros = useMemo(
    () => Array.from(new Set((recurso.datos?.productos ?? []).map((p) => p.category_name ?? 'Sin rubro'))).sort(),
    [recurso.datos],
  )

  const filtrados = useMemo(() => {
    const texto = busqueda.trim().toLowerCase()
    return (recurso.datos?.productos ?? []).filter((producto) => {
      if (rubro && (producto.category_name ?? 'Sin rubro') !== rubro) return false
      if (!texto) return true
      return `${producto.code} ${producto.description}`.toLowerCase().includes(texto)
    })
  }, [recurso.datos, rubro, busqueda])

  const stockBajo = useMemo(
    () => (recurso.datos?.stock ?? []).filter((fila) => fila.stock <= STOCK_BAJO),
    [recurso.datos],
  )

  return (
    <Pagina
      titulo="Productos"
      subtitulo="El catálogo con su rubro y su stock. Tocá un artículo para ver cómo se movió su precio."
    >
      <Bloque recurso={recurso} que="Cargando el catálogo">
        {(datos) => (
          <div className="pila">
            <div className="grilla g4">
              <Metrica rotulo="Artículos" valor={numero(datos.productos.length)} pie="en el catálogo" />
              <Metrica rotulo="Stock bajo" valor={numero(stockBajo.length)} pie={`${STOCK_BAJO} unidades o menos`} tono="urgente" />
              <Metrica rotulo="Sin rubro asignado" valor={numero(datos.sin_rubro.length)} pie="esperan que alguien decida" tono={datos.sin_rubro.length ? 'aviso' : 'neutro'} />
              <Metrica rotulo="Nuevos" valor={numero(datos.nuevos.length)} pie="aparecieron en la última pasada" />
            </div>

            <div className="grilla g2">
              <Panel titulo="Stock bajo" nota={`${STOCK_BAJO} unidades o menos`} alerta pegado>
                {stockBajo.length === 0 ? (
                  <Vacio>Ningún artículo está por debajo del mínimo.</Vacio>
                ) : (
                  <TablaCaja alto={300}>
                    <table className="tabla">
                      <thead>
                        <tr><th>Código</th><th>Descripción</th><th>Rubro</th><th className="num">Stock</th><th className="num">Precio</th></tr>
                      </thead>
                      <tbody>
                        {stockBajo.map((fila) => (
                          <tr key={fila.id} className="clickeable" onClick={() => setElegido(fila.id)}>
                            <td className="mono">{fila.code}</td>
                            <td>{fila.description}</td>
                            <td className="tenue">{fila.category}</td>
                            <td className={fila.stock === 0 ? 'num rojo fuerte' : 'num ambar fuerte'}>{numero(fila.stock)}</td>
                            <td className="num">{pesos(fila.price_cents)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </TablaCaja>
                )}
              </Panel>

              <Panel titulo="Productos nuevos" nota="aparecidos en la última actualización" pegado>
                {datos.nuevos.length === 0 ? (
                  <Vacio>No entraron productos nuevos en la última pasada.</Vacio>
                ) : (
                  <TablaCaja alto={300}>
                    <table className="tabla">
                      <thead>
                        <tr><th>Código</th><th>Descripción</th><th>Desde</th><th className="num">Precio</th></tr>
                      </thead>
                      <tbody>
                        {datos.nuevos.map((producto) => (
                          <tr key={producto.id} className="clickeable" onClick={() => setElegido(producto.id)}>
                            <td className="mono">{producto.code}</td>
                            <td>{producto.description}</td>
                            <td className="num">{fecha(producto.first_seen)}</td>
                            <td className="num">{pesos(producto.price_cents)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </TablaCaja>
                )}
              </Panel>
            </div>

            <Panel
              titulo="Catálogo"
              nota={`${filtrados.length} de ${datos.productos.length} artículos`}
              acciones={
                <div className="fila" style={{ gap: 10 }}>
                  <Campo etiqueta="">
                    <select value={rubro} onChange={(evento) => setRubro(evento.target.value)}>
                      <option value="">Todos los rubros</option>
                      {rubros.map((nombre) => <option key={nombre} value={nombre}>{nombre}</option>)}
                    </select>
                  </Campo>
                  <Campo etiqueta="">
                    <input
                      value={busqueda}
                      onChange={(evento) => setBusqueda(evento.target.value)}
                      placeholder="Buscar código o descripción"
                      style={{ minWidth: 240 }}
                    />
                  </Campo>
                </div>
              }
              pegado
            >
              {filtrados.length === 0 ? (
                <Vacio>No hay artículos que cumplan con el filtro.</Vacio>
              ) : (
                <TablaCaja alto={520}>
                  <table className="tabla">
                    <thead>
                      <tr>
                        <th>Código</th>
                        <th>Descripción</th>
                        <th>Rubro</th>
                        <th>Subrubro</th>
                        <th className="num">Precio</th>
                        <th className="num">Stock</th>
                        <th className="num">Última lectura</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtrados.map((producto) => (
                        <tr key={producto.id} className="clickeable" onClick={() => setElegido(producto.id)}>
                          <td className="mono">{producto.code}</td>
                          <td>{producto.description}</td>
                          <td>
                            {producto.category_name
                              ? producto.category_name
                              : <Chapa tono="parcial">sin rubro</Chapa>}
                          </td>
                          <td className="tenue">{producto.subcategory ?? '-'}</td>
                          <td className="num fuerte">{pesos(producto.price_cents)}</td>
                          <td className={producto.stock <= STOCK_BAJO ? 'num rojo fuerte' : 'num'}>{numero(producto.stock)}</td>
                          <td className="num tenue">{fecha(producto.last_seen)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </TablaCaja>
              )}
            </Panel>
          </div>
        )}
      </Bloque>

      {elegido === null ? null : <ModalPrecios id={elegido} onCerrar={() => setElegido(null)} />}
    </Pagina>
  )
}
