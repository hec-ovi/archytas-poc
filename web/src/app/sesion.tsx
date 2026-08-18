// Who is logged in, and what sections that gives them.

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../lib/api'
import { ApiError, mensajeDeError } from '../lib/errors'
import type { Seccion, Sesion } from '../lib/types'

interface ValorSesion {
  sesion: Sesion | null
  verificando: boolean
  /** Set when the api could not be reached at all, which is not the same as being logged out. */
  sinServidor: string | null
  entrar: (usuario: string, clave: string) => Promise<void>
  salir: () => Promise<void>
  reintentar: () => void
  puede: (seccion: Seccion) => boolean
}

const Contexto = createContext<ValorSesion | null>(null)

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(null)
  const [verificando, setVerificando] = useState(true)
  const [sinServidor, setSinServidor] = useState<string | null>(null)
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    let vivo = true
    setVerificando(true)
    api.acceso
      .quienSoy()
      .then((quien) => {
        if (!vivo) return
        setSesion(quien)
        setSinServidor(null)
      })
      .catch((problema) => {
        if (!vivo) return
        // 401 just means nobody is logged in yet; anything else means the api is not answering
        if (problema instanceof ApiError && problema.sinSesion) setSinServidor(null)
        else setSinServidor(mensajeDeError(problema))
      })
      .finally(() => { if (vivo) setVerificando(false) })
    return () => { vivo = false }
  }, [intento])

  const entrar = useCallback(async (usuario: string, clave: string) => {
    setSesion(await api.acceso.entrar(usuario, clave))
    setSinServidor(null)
  }, [])

  const reintentar = useCallback(() => setIntento((valor) => valor + 1), [])

  const salir = useCallback(async () => {
    try {
      await api.acceso.salir()
    } finally {
      setSesion(null)
    }
  }, [])

  const valor = useMemo<ValorSesion>(() => ({
    sesion,
    verificando,
    sinServidor,
    entrar,
    salir,
    reintentar,
    puede: (seccion) => Boolean(sesion?.secciones.includes(seccion)),
  }), [sesion, verificando, sinServidor, entrar, salir, reintentar])

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useSesion(): ValorSesion {
  const valor = useContext(Contexto)
  if (!valor) throw new Error('useSesion fuera del proveedor de sesion')
  return valor
}
