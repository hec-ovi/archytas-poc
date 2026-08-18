// The two numbers the rail shows as badges, kept fresh by the live channel.

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../lib/api'
import { useEventoVivo } from '../lib/useCanalVivo'
import { useSesion } from './sesion'

interface Contadores {
  revision: number | null
  mensajes: number | null
  refrescarMensajes: () => void
  refrescarRevision: () => void
}

const Contexto = createContext<Contadores>({
  revision: null, mensajes: null, refrescarMensajes: () => {}, refrescarRevision: () => {},
})

export function ProveedorContadores({ children }: { children: ReactNode }) {
  const { puede } = useSesion()
  const tieneRevision = puede('revision')
  const tieneMensajes = puede('mensajes')
  const [revision, setRevision] = useState<number | null>(null)
  const [mensajes, setMensajes] = useState<number | null>(null)

  const refrescarRevision = useCallback(() => {
    if (!tieneRevision) return
    api.revision.listar().then((datos) => setRevision(datos.pendientes.length)).catch(() => setRevision(null))
  }, [tieneRevision])

  const refrescarMensajes = useCallback(() => {
    if (!tieneMensajes) return
    api.mensajes.listar(true).then((datos) => setMensajes(datos.abiertos)).catch(() => setMensajes(null))
  }, [tieneMensajes])

  useEffect(() => { refrescarRevision() }, [refrescarRevision])
  useEffect(() => { refrescarMensajes() }, [refrescarMensajes])

  useEventoVivo('revision-cambio', (datos) => {
    if (typeof datos.pendientes === 'number') setRevision(datos.pendientes)
  })
  useEventoVivo('sincronizacion-lista', () => {
    refrescarRevision()
    refrescarMensajes()
  })

  const valor = useMemo(
    () => ({ revision, mensajes, refrescarMensajes, refrescarRevision }),
    [revision, mensajes, refrescarMensajes, refrescarRevision],
  )
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useContadores(): Contadores {
  return useContext(Contexto)
}
