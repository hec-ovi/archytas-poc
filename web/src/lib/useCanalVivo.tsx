// The one hook every screen uses to hear the server. One socket, many listeners.

import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { CanalVivo, type EstadoCanal } from './canal'
import type { EventoVivo } from './types'

const Contexto = createContext<CanalVivo | null>(null)

export function ProveedorCanal({ children }: { children: ReactNode }) {
  const canal = useMemo(() => new CanalVivo(), [])
  useEffect(() => {
    canal.abrir()
    return () => canal.cerrar()
  }, [canal])
  return <Contexto.Provider value={canal}>{children}</Contexto.Provider>
}

function usarCanal(): CanalVivo | null {
  return useContext(Contexto)
}

/** Run `manejar` every time the server broadcasts `evento`. */
export function useEventoVivo(evento: EventoVivo, manejar: (datos: Record<string, unknown>) => void): void {
  const canal = usarCanal()
  const ultimo = useRef(manejar)
  ultimo.current = manejar

  useEffect(() => {
    if (!canal) return
    return canal.escuchar(evento, (datos) => ultimo.current(datos))
  }, [canal, evento])
}

/** Whether the live channel is up, for the discreet indicator in the header. */
export function useEstadoCanal(): EstadoCanal {
  const canal = usarCanal()
  const [estado, setEstado] = useState<EstadoCanal>(canal?.estado ?? 'conectando')
  useEffect(() => {
    if (!canal) return
    return canal.observarEstado(setEstado)
  }, [canal])
  return estado
}
