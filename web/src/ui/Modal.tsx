import { useEffect } from 'react'
import type { ReactNode } from 'react'

interface Props {
  titulo: ReactNode
  onCerrar: () => void
  children: ReactNode
  ancho?: boolean
  angosto?: boolean
  acciones?: ReactNode
}

export function Modal({ titulo, onCerrar, children, ancho, angosto, acciones }: Props) {
  useEffect(() => {
    const escuchar = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') onCerrar()
    }
    window.addEventListener('keydown', escuchar)
    return () => window.removeEventListener('keydown', escuchar)
  }, [onCerrar])

  return (
    <div className="telon" onMouseDown={(evento) => { if (evento.target === evento.currentTarget) onCerrar() }}>
      <div className={['modal', ancho ? 'ancho' : '', angosto ? 'angosto' : ''].filter(Boolean).join(' ')} role="dialog" aria-modal="true">
        <header className="modal-cabecera">
          <div className="fila" style={{ gap: 10 }}>{titulo}</div>
          <div className="fila">
            {acciones}
            <button className="cerrar" onClick={onCerrar} aria-label="Cerrar">×</button>
          </div>
        </header>
        <div className="modal-cuerpo">{children}</div>
      </div>
    </div>
  )
}
