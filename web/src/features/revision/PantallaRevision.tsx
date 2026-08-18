import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { useRecurso } from '../../lib/useRecurso'
import { useEventoVivo } from '../../lib/useCanalVivo'
import { numero } from '../../lib/format'
import { Pagina } from '../../app/Pagina'
import { useContadores } from '../../app/contadores'
import { Panel } from '../../ui/Panel'
import { Metrica } from '../../ui/Metrica'
import { Pestanias } from '../../ui/Pestanias'
import { Bloque, Vacio } from '../../ui/Estado'
import { TarjetaPendiente } from './TarjetaPendiente'
import type { VentaExcluida } from '../../lib/types'
import './revision.css'

const TIPO_TEXTO: Record<string, string> = {
  'venta-duplicada': 'Ventas duplicadas',
  'venta-rota': 'Ventas rotas',
  proveedor: 'Proveedores',
  rubro: 'Rubros',
}

export function PantallaRevision() {
  const recurso = useRecurso(() => api.revision.listar(), [])
  const { refrescarRevision } = useContadores()
  const [tipo, setTipo] = useState<string>('')
  const [trabajando, setTrabajando] = useState<number | null>(null)
  const [ultimo, setUltimo] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [resueltos, setResueltos] = useState(0)

  // duplicate rows are matched against the excluded sales to find their row hash;
  // a role without the sales section simply gets the choice disabled with a reason
  const [excluidas, setExcluidas] = useState<VentaExcluida[] | null>(null)
  useEffect(() => {
    let vivo = true
    api.ventas()
      .then((datos) => { if (vivo) setExcluidas(datos.excluidas) })
      .catch(() => { if (vivo) setExcluidas(null) })
    return () => { vivo = false }
  }, [])

  useEventoVivo('sincronizacion-lista', () => recurso.recargar())

  const sacar = useCallback((id: number) => {
    recurso.fijar((actual) => actual && {
      ...actual,
      pendientes: actual.pendientes.filter((item) => item.id !== id),
    })
    setResueltos((valor) => valor + 1)
    refrescarRevision()
  }, [recurso, refrescarRevision])

  const resolver = async (id: number, decision: Record<string, unknown>) => {
    setTrabajando(id)
    setError(null)
    try {
      const respuesta = await api.revision.resolver(id, decision)
      setUltimo(respuesta.aplicado)
      sacar(id)
    } catch (problema) {
      setError(mensajeDeError(problema))
    } finally {
      setTrabajando(null)
    }
  }

  const descartar = async (id: number) => {
    setTrabajando(id)
    setError(null)
    try {
      await api.revision.descartar(id)
      setUltimo('Se sacó de la cola sin cambiar nada.')
      sacar(id)
    } catch (problema) {
      setError(mensajeDeError(problema))
    } finally {
      setTrabajando(null)
    }
  }

  const pendientes = useMemo(
    () => (recurso.datos?.pendientes ?? []).filter((item) => !tipo || item.kind === tipo),
    [recurso.datos, tipo],
  )

  const opciones = useMemo(() => [
    { clave: '', texto: 'Todo', cuenta: recurso.datos?.pendientes.length ?? 0 },
    ...(recurso.datos?.resumen ?? []).map((fila) => ({
      clave: fila.kind,
      texto: TIPO_TEXTO[fila.kind] ?? fila.kind,
      cuenta: fila.n,
    })),
  ], [recurso.datos])

  return (
    <Pagina
      titulo="Revisión"
      subtitulo="Lo que el sistema no quiso adivinar. Cada uno se resuelve en un clic y la decisión queda para siempre."
    >
      <Bloque recurso={recurso} que="Cargando la cola de revisión">
        {(datos) => (
          <div className="pila">
            <div className="grilla g4">
              <Metrica
                rotulo="Esperan decisión"
                valor={numero(datos.pendientes.length)}
                pie="cada uno bloquea datos de sumar"
                tono={datos.pendientes.length ? 'urgente' : 'calma'}
              />
              {datos.resumen.map((fila) => (
                <Metrica
                  key={fila.kind}
                  rotulo={TIPO_TEXTO[fila.kind] ?? fila.kind}
                  valor={numero(fila.n)}
                  pie="en la cola"
                />
              ))}
              <Metrica rotulo="Resueltos ahora" valor={numero(resueltos)} pie="en esta sesión" tono="calma" />
            </div>

            {error ? <div className="aviso error">{error}</div> : null}
            {ultimo && !error ? <div className="aviso exito">{ultimo}</div> : null}

            <Panel titulo="Cola de pendientes" nota={`${pendientes.length} en pantalla`} pegado>
              <Pestanias opciones={opciones} activa={tipo} onCambiar={setTipo} />
              <div className="pila" style={{ padding: 12 }}>
                {pendientes.length === 0 ? (
                  <Vacio>No queda nada esperando una decisión. Buen trabajo.</Vacio>
                ) : (
                  pendientes.map((pendiente) => (
                    <TarjetaPendiente
                      key={pendiente.id}
                      pendiente={pendiente}
                      excluidas={excluidas}
                      trabajando={trabajando === pendiente.id}
                      onResolver={(decision) => void resolver(pendiente.id, decision)}
                      onDescartar={() => void descartar(pendiente.id)}
                    />
                  ))
                )}
              </div>
            </Panel>
          </div>
        )}
      </Bloque>
    </Pagina>
  )
}
