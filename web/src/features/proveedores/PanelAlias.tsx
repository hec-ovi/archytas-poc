import { Chapa } from '../../ui/Chapa'
import { Panel } from '../../ui/Panel'
import { Vacio } from '../../ui/Estado'
import type { Alias, Proveedor } from '../../lib/types'

const METODO: Record<string, string> = {
  signature: 'por CUIT o mail idéntico',
  persona: 'lo decidió una persona',
  exacto: 'coincide exacto',
  parecido: 'por parecido de nombre',
}

/** The client's "the same supplier shows up three or four different ways", shown as solved. */
export function PanelAlias({ proveedor, alias }: { proveedor: Proveedor; alias: Alias[] }) {
  return (
    <Panel
      titulo="Cómo aparece escrito"
      nota={`${alias.length + 1} formas unificadas en este proveedor`}
      pegado
    >
      <ul className="lista-simple">
        <li className="fila" style={{ justifyContent: 'space-between' }}>
          <span className="fuerte">{proveedor.name}</span>
          <Chapa tono="acento">nombre canónico</Chapa>
        </li>
        {alias.map((forma) => (
          <li key={forma.id} className="fila" style={{ justifyContent: 'space-between', gap: 12 }}>
            <span className="mono">{forma.spelling}</span>
            <span className="fila" style={{ gap: 8 }}>
              <span className="tenue" style={{ fontSize: 11.5 }}>{METODO[forma.method] ?? forma.method}</span>
              <Chapa>{Math.round(forma.confidence * 100)}%</Chapa>
            </span>
          </li>
        ))}
      </ul>
      {alias.length === 0 ? <Vacio>Este proveedor siempre llegó escrito igual.</Vacio> : null}
    </Panel>
  )
}
