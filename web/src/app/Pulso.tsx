import { useEstadoCanal } from '../lib/useCanalVivo'

const TEXTO = {
  'en-vivo': 'En vivo',
  conectando: 'Conectando',
  caido: 'Sin conexión en vivo',
} as const

/** The discreet sign that changes made by someone else land here on their own. */
export function Pulso() {
  const estado = useEstadoCanal()
  return (
    <span className={`pulso ${estado}`} title="Los cambios de otras personas aparecen sin recargar la página">
      <span className="punto" />
      {TEXTO[estado]}
    </span>
  )
}
