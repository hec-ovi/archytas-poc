type Tono = 'acento' | 'rojo' | 'ambar' | 'verde'

export function Barrita({ parte, total, tono = 'acento' }: { parte: number; total: number; tono?: Tono }) {
  const ancho = total > 0 ? Math.min(100, Math.max(0, (parte / total) * 100)) : 0
  return (
    <div className={['barrita', tono === 'acento' ? '' : tono].filter(Boolean).join(' ')}>
      <span style={{ width: `${ancho}%` }} />
    </div>
  )
}
