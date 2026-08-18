import { useMemo, useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { useRecurso } from '../../lib/useRecurso'
import { useEventoVivo } from '../../lib/useCanalVivo'
import { numero } from '../../lib/format'
import { Pagina } from '../../app/Pagina'
import { useContadores } from '../../app/contadores'
import { Panel } from '../../ui/Panel'
import { Metrica } from '../../ui/Metrica'
import { Campo } from '../../ui/Campo'
import { Bloque, Vacio } from '../../ui/Estado'
import { ModalFactura } from '../facturas/ModalFactura'
import { FilaMensaje } from './FilaMensaje'
import { TIPO_MENSAJE } from '../../lib/etiquetas'
import './mensajes.css'

export function PantallaMensajes() {
  const [soloAbiertos, setSoloAbiertos] = useState(true)
  const recurso = useRecurso(() => api.mensajes.listar(soloAbiertos), [soloAbiertos])
  const { refrescarMensajes } = useContadores()
  const [tipo, setTipo] = useState('')
  const [trabajando, setTrabajando] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [factura, setFactura] = useState<number | null>(null)

  useEventoVivo('sincronizacion-lista', () => recurso.recargar())

  const resolver = async (id: number) => {
    setTrabajando(id)
    setError(null)
    try {
      await api.mensajes.resolver(id)
      recurso.recargar()
      refrescarMensajes()
    } catch (problema) {
      setError(mensajeDeError(problema))
    } finally {
      setTrabajando(null)
    }
  }

  const filas = useMemo(
    () => (recurso.datos?.mensajes ?? []).filter((mensaje) => !tipo || mensaje.kind === tipo),
    [recurso.datos, tipo],
  )

  return (
    <Pagina
      titulo="Mensajes"
      subtitulo="Lo que llega del portal y de los proveedores. Se cierra acá, no en el mail."
    >
      <Bloque recurso={recurso} que="Cargando la bandeja">
        {(datos) => (
          <div className="pila">
            <div className="grilla g4">
              <Metrica
                rotulo="Abiertos"
                valor={numero(datos.abiertos)}
                pie="sin resolver"
                tono={datos.abiertos ? 'urgente' : 'calma'}
              />
              {datos.por_tipo.map((fila) => (
                <Metrica
                  key={fila.kind}
                  rotulo={TIPO_MENSAJE[fila.kind] ?? fila.kind}
                  valor={numero(fila.open)}
                  pie={`${numero(fila.n)} en total`}
                />
              ))}
            </div>

            {error ? <div className="aviso error">{error}</div> : null}

            <Panel
              titulo="Bandeja"
              nota={`${filas.length} mensajes en pantalla`}
              acciones={
                <div className="fila" style={{ gap: 12 }}>
                  <Campo etiqueta="">
                    <select value={tipo} onChange={(evento) => setTipo(evento.target.value)}>
                      <option value="">Todos los tipos</option>
                      {datos.por_tipo.map((fila) => (
                        <option key={fila.kind} value={fila.kind}>
                          {TIPO_MENSAJE[fila.kind] ?? fila.kind} ({fila.n})
                        </option>
                      ))}
                    </select>
                  </Campo>
                  <label className="fila" style={{ gap: 6 }}>
                    <input
                      type="checkbox"
                      checked={soloAbiertos}
                      onChange={(evento) => setSoloAbiertos(evento.target.checked)}
                    />
                    <span>Solo sin resolver</span>
                  </label>
                </div>
              }
              pegado
            >
              {filas.length === 0 ? (
                <Vacio>No hay mensajes que cumplan con el filtro.</Vacio>
              ) : (
                <ul className="lista-simple">
                  {filas.map((mensaje) => (
                    <FilaMensaje
                      key={mensaje.id}
                      mensaje={mensaje}
                      trabajando={trabajando === mensaje.id}
                      onResolver={() => void resolver(mensaje.id)}
                      onAbrirFactura={setFactura}
                    />
                  ))}
                </ul>
              )}
            </Panel>
          </div>
        )}
      </Bloque>

      {factura === null ? null : <ModalFactura id={factura} onCerrar={() => setFactura(null)} />}
    </Pagina>
  )
}
