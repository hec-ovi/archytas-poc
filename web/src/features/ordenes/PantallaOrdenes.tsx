import { useMemo, useState } from 'react'
import { api } from '../../lib/api'
import { useRecurso } from '../../lib/useRecurso'
import { useEventoVivo } from '../../lib/useCanalVivo'
import { numero, pesos } from '../../lib/format'
import { Pagina } from '../../app/Pagina'
import { Panel } from '../../ui/Panel'
import { Metrica } from '../../ui/Metrica'
import { Campo } from '../../ui/Campo'
import { Bloque } from '../../ui/Estado'
import { TablaOrdenes } from './TablaOrdenes'

const NOMBRE_ESTADO: Record<string, string> = {
  'por-enviar': 'Por enviar',
  enviada: 'Enviada',
  confirmada: 'Confirmada',
  recibida: 'Recibida',
}

export function PantallaOrdenes() {
  const recurso = useRecurso(() => api.ordenes(), [])
  const [estado, setEstado] = useState('')
  const [busqueda, setBusqueda] = useState('')

  useEventoVivo('sincronizacion-lista', () => recurso.recargar())

  const filtradas = useMemo(() => {
    const texto = busqueda.trim().toLowerCase()
    return (recurso.datos?.ordenes ?? []).filter((orden) => {
      if (estado && orden.status !== estado) return false
      if (!texto) return true
      return `${orden.number} ${orden.supplier_name ?? ''} ${orden.product_description ?? ''}`
        .toLowerCase().includes(texto)
    })
  }, [recurso.datos, estado, busqueda])

  const olvidadasCentavos = (recurso.datos?.olvidadas ?? []).reduce((suma, orden) => suma + orden.estimated_cents, 0)

  return (
    <Pagina
      titulo="Órdenes de compra"
      subtitulo="Primero las que quedaron abiertas demasiado tiempo, después todo el resto."
    >
      <Bloque recurso={recurso} que="Cargando las órdenes">
        {(datos) => (
          <div className="pila">
            <div className="grilla g4">
              <Metrica
                rotulo="Olvidadas"
                valor={numero(datos.olvidadas.length)}
                pie={`abiertas hace más de ${datos.dias_para_olvidada} días · ${pesos(olvidadasCentavos)}`}
                tono="urgente"
              />
              {datos.por_estado.map((fila) => (
                <Metrica
                  key={fila.status}
                  rotulo={NOMBRE_ESTADO[fila.status] ?? fila.status}
                  valor={numero(fila.n)}
                  pie={pesos(fila.cents)}
                />
              ))}
            </div>

            <Panel
              titulo="Órdenes olvidadas"
              nota={`sin recibir hace más de ${datos.dias_para_olvidada} días`}
              alerta
              pegado
            >
              <TablaOrdenes
                ordenes={datos.olvidadas}
                limiteDias={datos.dias_para_olvidada}
                alto={340}
                vacio="Ninguna orden quedó olvidada."
              />
            </Panel>

            <Panel
              titulo="Todas las órdenes"
              nota={`${filtradas.length} de ${datos.ordenes.length}`}
              acciones={
                <div className="fila" style={{ gap: 10 }}>
                  <Campo etiqueta="">
                    <select value={estado} onChange={(evento) => setEstado(evento.target.value)}>
                      <option value="">Todos los estados</option>
                      {datos.por_estado.map((fila) => (
                        <option key={fila.status} value={fila.status}>
                          {NOMBRE_ESTADO[fila.status] ?? fila.status} ({fila.n})
                        </option>
                      ))}
                    </select>
                  </Campo>
                  <Campo etiqueta="">
                    <input
                      value={busqueda}
                      onChange={(evento) => setBusqueda(evento.target.value)}
                      placeholder="Buscar orden, proveedor o producto"
                      style={{ minWidth: 240 }}
                    />
                  </Campo>
                </div>
              }
              pegado
            >
              <TablaOrdenes
                ordenes={filtradas}
                limiteDias={datos.dias_para_olvidada}
                alto={460}
                vacio="No hay órdenes que cumplan con el filtro."
              />
            </Panel>
          </div>
        )}
      </Bloque>
    </Pagina>
  )
}
