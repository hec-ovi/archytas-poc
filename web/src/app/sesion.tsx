// Who is logged in, and what sections that gives them.

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../lib/api'
import { ApiError, mensajeDeError } from '../lib/errors'
import type { Seccion, Sesion } from '../lib/types'

interface ValorSesion {
  sesion: Sesion | null
  verificando: boolean
  entrar: (usuario: string, clave: string) => Promise<void>
  salir: () => Promise<void>
  puede: (seccion: Seccion) => boolean
}

const Contexto = createContext<ValorSesion | null>(null)

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(null)
  const [verificando, setVerificando] = useState(true)

  useEffect(() => {
    let vivo = true
    api.acceso
      .quienSoy()
      .then((quien) => { if (vivo) setSesion(quien) })
      .catch((problema) => {
        // 401 just means nobody is logged in yet; anything else is worth knowing about
        if (!(problema instanceof ApiError) || !problema.sinSesion) console.warn(mensajeDeError(problema))
      })
      .finally(() => { if (vivo) setVerificando(false) })
    return () => { vivo = false }
  }, [])

  const entrar = useCallback(async (usuario: string, clave: string) => {
    setSesion(await api.acceso.entrar(usuario, clave))
  }, [])

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
    entrar,
    salir,
    puede: (seccion) => Boolean(sesion?.secciones.includes(seccion)),
  }), [sesion, verificando, entrar, salir])

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function useSesion(): ValorSesion {
  const valor = useContext(Contexto)
  if (!valor) throw new Error('useSesion fuera del proveedor de sesion')
  return valor
}
