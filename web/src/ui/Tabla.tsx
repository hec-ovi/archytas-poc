import type { ReactNode } from 'react'

/** Wide tables scroll inside this box, never the page. */
export function TablaCaja({ children, alto }: { children: ReactNode; alto?: number }) {
  return (
    <div className="tabla-caja" style={alto ? { maxHeight: alto } : undefined}>
      {children}
    </div>
  )
}
