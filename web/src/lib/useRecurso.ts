// Loading, error and reload for one api call. Every screen states what it is doing.

import { useCallback, useEffect, useRef, useState } from 'react'
import { mensajeDeError } from './errors'

export interface Recurso<T> {
  datos: T | null
  cargando: boolean
  error: string | null
  recargar: () => void
  /** Patch what is already loaded without a round trip. */
  fijar: (siguiente: T) => void
}

export function useRecurso<T>(traer: () => Promise<T>, dependencias: unknown[] = []): Recurso<T> {
  const [datos, setDatos] = useState<T | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const vivo = useRef(true)

  // the caller writes the fetcher inline, so it is keyed by its declared dependencies
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const pedir = useCallback(traer, dependencias)

  const correr = useCallback(() => {
    setCargando(true)
    setError(null)
    pedir()
      .then((respuesta) => {
        if (vivo.current) setDatos(respuesta)
      })
      .catch((problema) => {
        if (vivo.current) setError(mensajeDeError(problema))
      })
      .finally(() => {
        if (vivo.current) setCargando(false)
      })
  }, [pedir])

  useEffect(() => {
    vivo.current = true
    correr()
    return () => {
      vivo.current = false
    }
  }, [correr])

  return { datos, cargando, error, recargar: correr, fijar: setDatos }
}
