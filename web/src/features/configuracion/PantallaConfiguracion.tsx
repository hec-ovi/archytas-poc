import { useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { useRecurso } from '../../lib/useRecurso'
import { useEventoVivo } from '../../lib/useCanalVivo'
import { Pagina } from '../../app/Pagina'
import { Panel } from '../../ui/Panel'
import { Bloque } from '../../ui/Estado'
import { FilaParametro } from './FilaParametro'
import { PanelSync } from './PanelSync'

export function PantallaConfiguracion() {
  const parametros = useRecurso(() => api.configuracion.listar(), [])
  const sincronizacion = useRecurso(() => api.sync.estado(), [])
  const [guardado, setGuardado] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEventoVivo('sincronizacion-lista', () => {
    sincronizacion.recargar()
    parametros.recargar()
  })

  const guardar = async (key: string, valor: number) => {
    setError(null)
    try {
      const respuesta = await api.configuracion.guardar(key, valor)
      parametros.fijar(respuesta)
      setGuardado('Listo, el cambio ya está aplicado.')
    } catch (problema) {
      setError(mensajeDeError(problema))
      throw problema
    }
  }

  return (
    <Pagina
      titulo="Configuración"
      subtitulo="Los números que gobiernan los avisos y la actualización automática."
    >
      <div className="pila">
        {guardado && !error ? <div className="aviso exito">{guardado}</div> : null}
        {error ? <div className="aviso error">{error}</div> : null}

        <Panel titulo="Parámetros" nota="cada cambio queda con tu nombre y la fecha" pegado>
          <Bloque recurso={parametros} que="Cargando los parámetros">
            {(datos) => (
              <ul className="lista-simple">
                {datos.configuracion.map((parametro) => (
                  <FilaParametro key={parametro.key} parametro={parametro} onGuardar={guardar} />
                ))}
              </ul>
            )}
          </Bloque>
        </Panel>

        <PanelSync recurso={sincronizacion} />
      </div>
    </Pagina>
  )
}
