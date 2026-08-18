import { useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { fechaHora, numero } from '../../lib/format'
import { Boton } from '../../ui/Boton'
import { Chapa } from '../../ui/Chapa'
import { Panel } from '../../ui/Panel'
import { TablaCaja } from '../../ui/Tabla'
import { Bloque } from '../../ui/Estado'
import type { Recurso } from '../../lib/useRecurso'
import type { EstadoSync } from '../../lib/types'

/** Run a pass now, and show what the last ones did. */
export function PanelSync({ recurso }: { recurso: Recurso<EstadoSync> }) {
  const [lanzando, setLanzando] = useState(false)
  const [aviso, setAviso] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const lanzar = async (conHistorial: boolean) => {
    setLanzando(true)
    setError(null)
    setAviso(null)
    try {
      await api.sync.lanzar(conHistorial)
      setAviso('La actualización arrancó. Cuando termine, la pantalla se actualiza sola.')
    } catch (problema) {
      setError(mensajeDeError(problema))
    } finally {
      setLanzando(false)
    }
  }

  return (
    <Panel
      titulo="Actualizar desde el portal"
      nota={recurso.datos?.ultima_ok ? `última buena: ${fechaHora(recurso.datos.ultima_ok.finished_at)}` : 'nunca corrió'}
      acciones={
        <>
          <Boton variante="principal" disabled={lanzando} onClick={() => void lanzar(false)}>
            {lanzando ? 'Lanzando…' : 'Actualizar ahora'}
          </Boton>
          <Boton disabled={lanzando} onClick={() => void lanzar(true)}>
            Actualizar con historial de precios
          </Boton>
        </>
      }
      pegado
    >
      <div style={{ padding: 12 }}>
        {aviso ? <div className="aviso exito">{aviso}</div> : null}
        {error ? <div className="aviso error">{error}</div> : null}
      </div>

      <Bloque recurso={recurso} que="Cargando el estado de las actualizaciones">
        {(datos) => (
          <TablaCaja alto={280}>
            <table className="tabla">
              <thead>
                <tr>
                  <th>Arrancó</th>
                  <th>Terminó</th>
                  <th>Origen</th>
                  <th>Estado</th>
                  <th className="num">Guardados</th>
                  <th className="num">A revisión</th>
                </tr>
              </thead>
              <tbody>
                {datos.pasadas.map((pasada) => (
                  <tr key={pasada.id}>
                    <td className="num">{fechaHora(pasada.started_at)}</td>
                    <td className="num">{fechaHora(pasada.finished_at)}</td>
                    <td className="tenue">{pasada.trigger}</td>
                    <td><Chapa tono={pasada.status === 'ok' ? 'saldada' : 'impaga'}>{pasada.status}</Chapa></td>
                    <td className="num">{numero(pasada.summary?.guardados ?? 0)}</td>
                    <td className="num">{numero(pasada.summary?.a_revision ?? 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TablaCaja>
        )}
      </Bloque>
    </Panel>
  )
}
