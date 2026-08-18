// The live channel: one socket for the whole page, reconnecting on its own.

import { wsUrl } from './config'
import type { EventoVivo, MensajeVivo } from './types'

export type EstadoCanal = 'conectando' | 'en-vivo' | 'caido'

type Oyente = (datos: Record<string, unknown>) => void
type OyenteEstado = (estado: EstadoCanal) => void

const REINTENTO_MS = 3000

export class CanalVivo {
  private socket: WebSocket | null = null
  private oyentes = new Map<EventoVivo, Set<Oyente>>()
  private oyentesEstado = new Set<OyenteEstado>()
  private reintento: ReturnType<typeof setTimeout> | null = null
  private cerrado = false
  private _estado: EstadoCanal = 'conectando'

  get estado(): EstadoCanal {
    return this._estado
  }

  abrir(): void {
    this.cerrado = false
    this.conectar()
  }

  cerrar(): void {
    this.cerrado = true
    if (this.reintento) clearTimeout(this.reintento)
    this.socket?.close()
    this.socket = null
  }

  /** Subscribe to one event. Returns the unsubscribe function. */
  escuchar(evento: EventoVivo, oyente: Oyente): () => void {
    const grupo = this.oyentes.get(evento) ?? new Set<Oyente>()
    grupo.add(oyente)
    this.oyentes.set(evento, grupo)
    return () => grupo.delete(oyente)
  }

  observarEstado(oyente: OyenteEstado): () => void {
    this.oyentesEstado.add(oyente)
    oyente(this._estado)
    return () => this.oyentesEstado.delete(oyente)
  }

  private conectar(): void {
    if (this.cerrado) return
    this.anunciar('conectando')
    let socket: WebSocket
    try {
      socket = new WebSocket(wsUrl())
    } catch {
      this.programarReintento()
      return
    }
    this.socket = socket

    socket.onopen = () => this.anunciar('en-vivo')
    socket.onmessage = (evento) => this.repartir(evento.data)
    socket.onerror = () => socket.close()
    socket.onclose = () => {
      if (this.socket === socket) this.socket = null
      this.anunciar('caido')
      this.programarReintento()
    }
  }

  private programarReintento(): void {
    if (this.cerrado || this.reintento) return
    this.reintento = setTimeout(() => {
      this.reintento = null
      this.conectar()
    }, REINTENTO_MS)
  }

  private repartir(texto: unknown): void {
    if (typeof texto !== 'string') return
    let mensaje: MensajeVivo
    try {
      mensaje = JSON.parse(texto) as MensajeVivo
    } catch {
      return
    }
    for (const oyente of this.oyentes.get(mensaje.evento) ?? []) oyente(mensaje.datos ?? {})
  }

  private anunciar(estado: EstadoCanal): void {
    if (this._estado === estado) return
    this._estado = estado
    for (const oyente of this.oyentesEstado) oyente(estado)
  }
}
