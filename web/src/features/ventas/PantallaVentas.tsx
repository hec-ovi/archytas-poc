import { api } from '../../lib/api'
import { useRecurso } from '../../lib/useRecurso'
import { numero, mesCorto, pesos } from '../../lib/format'
import { Pagina } from '../../app/Pagina'
import { Panel } from '../../ui/Panel'
import { Metrica } from '../../ui/Metrica'
import { Bloque } from '../../ui/Estado'
import { TablaCaja } from '../../ui/Tabla'
import { SerieMensual } from '../../ui/graficos/SerieMensual'
import { BarrasCategoria } from '../../ui/graficos/BarrasCategoria'
import { BarraProporcion } from '../../ui/graficos/BarraProporcion'
import { ESTADO_VENTA } from '../../lib/etiquetas'
import { PanelExcluidas } from './PanelExcluidas'

export function PantallaVentas() {
  const recurso = useRecurso(() => api.ventas(), [])

  return (
    <Pagina
      titulo="Ventas"
      subtitulo="Los totales salen solo de las ventas que se pueden sumar. Las otras están listadas abajo con el motivo."
    >
      <Bloque recurso={recurso} que="Cargando las ventas">
        {(datos) => {
          const validas = datos.salud.valida ?? { count: 0, cents: 0 }
          const excluidasCentavos = datos.excluidas.reduce((suma, venta) => suma + (venta.total_cents ?? 0), 0)
          const ultimoMes = datos.por_mes[datos.por_mes.length - 1]

          return (
            <div className="pila">
              <div className="grilla g4">
                <Metrica rotulo="Facturado válido" valor={pesos(validas.cents)} pie={`${numero(validas.count)} ventas`} tono="calma" />
                <Metrica
                  rotulo="Último mes"
                  valor={ultimoMes ? pesos(ultimoMes.revenue_cents) : '-'}
                  pie={ultimoMes ? `${mesCorto(ultimoMes.month)} · ${numero(ultimoMes.sale_count)} ventas` : 'sin datos'}
                />
                <Metrica
                  rotulo="Fuera del total"
                  valor={numero(datos.excluidas.length)}
                  pie={`${pesos(excluidasCentavos)} sin sumar`}
                  tono="urgente"
                />
                <Metrica rotulo="Rubros con venta" valor={numero(datos.por_rubro.length)} pie="según el catálogo" />
              </div>

              <Panel titulo="Facturación por mes" nota="solo ventas válidas">
                <SerieMensual datos={datos.por_mes} alto={260} />
              </Panel>

              <div className="grilla g2">
                <Panel titulo="Facturación por rubro">
                  <BarrasCategoria
                    tituloValor="Facturado"
                    datos={datos.por_rubro
                      .slice()
                      .sort((a, b) => b.revenue_cents - a.revenue_cents)
                      .map((rubro) => ({
                        etiqueta: rubro.category,
                        valor: rubro.revenue_cents,
                        nota: `${numero(rubro.sale_count)} ventas`,
                      }))}
                  />
                </Panel>

                <Panel titulo="Salud de los datos de venta" nota="qué entra y qué queda afuera">
                  <BarraProporcion
                    tramos={Object.entries(datos.salud).map(([clave, valor]) => ({
                      clave,
                      texto: ESTADO_VENTA[clave] ?? clave,
                      cantidad: valor.count,
                      centavos: valor.cents,
                    }))}
                  />
                </Panel>
              </div>

              <div className="grilla g2">
                <Panel titulo="Productos que más facturan" pegado>
                  <TablaCaja alto={360}>
                    <table className="tabla">
                      <thead>
                        <tr><th>Código</th><th>Descripción</th><th className="num">Unidades</th><th className="num">Facturado</th></tr>
                      </thead>
                      <tbody>
                        {datos.productos_top.map((producto) => (
                          <tr key={producto.code}>
                            <td className="mono">{producto.code}</td>
                            <td>{producto.description}</td>
                            <td className="num">{numero(producto.units)}</td>
                            <td className="num fuerte">{pesos(producto.revenue_cents)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </TablaCaja>
                </Panel>

                <Panel titulo="Clientes que más compran" pegado>
                  <TablaCaja alto={360}>
                    <table className="tabla">
                      <thead>
                        <tr><th>Cliente</th><th className="num">Ventas</th><th className="num">Facturado</th></tr>
                      </thead>
                      <tbody>
                        {datos.clientes_top.map((cliente) => (
                          <tr key={cliente.customer}>
                            <td>{cliente.customer}</td>
                            <td className="num">{numero(cliente.sale_count)}</td>
                            <td className="num fuerte">{pesos(cliente.revenue_cents)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </TablaCaja>
                </Panel>
              </div>

              <PanelExcluidas excluidas={datos.excluidas} />
            </div>
          )
        }}
      </Bloque>
    </Pagina>
  )
}
