import type { ReactNode } from 'react'

interface Props {
  etiqueta: string
  ayuda?: ReactNode
  children: ReactNode
  className?: string
}

export function Campo({ etiqueta, ayuda, children, className }: Props) {
  return (
    <label className={['campo', className ?? ''].filter(Boolean).join(' ')}>
      <span>{etiqueta}</span>
      {children}
      {ayuda ? <span className="ayuda">{ayuda}</span> : null}
    </label>
  )
}
