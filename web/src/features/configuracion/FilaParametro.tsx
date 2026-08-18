import { useState } from 'react'
import { fechaHora } from '../../lib/format'
import { Boton } from '../../ui/Boton'
import { PRESENTACION, aFormulario, aGuardar } from './parametros'
import type { Parametro } from '../../lib/types'

interface Props {
  parametro: Parametro
  onGuardar: (key: string, valor: number) => Promise<void>
}

export function FilaParametro({ parametro, onGuardar }: Props) {
  const presentacion = PRESENTACION[parametro.key]
  const original = aFormulario(parametro.key, parametro.value)
  const [texto, setTexto] = useState(original)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cambiado = texto !== original

  const guardar = async () => {
    const valor = aGuardar(parametro.key, texto)
    if (valor === null || (presentacion?.minimo !== undefined && valor < presentacion.minimo)) {
      setError('Ese valor no sirve. Escribí un número.')
      return
    }
    setError(null)
    setGuardando(true)
    try {
      await onGuardar(parametro.key, valor)
    } catch (problema) {
      setError(problema instanceof Error ? problema.message : 'No se pudo guardar')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <li>
      <div className="fila" style={{ justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
        <div style={{ minWidth: 0 }}>
          <div className="fuerte">{presentacion?.titulo ?? parametro.label}</div>
          {presentacion ? <div className="tenue" style={{ fontSize: 11.5 }}>{presentacion.ayuda}</div> : null}
          <div className="tenue" style={{ fontSize: 11 }}>
            Último cambio: {fechaHora(parametro.updated_at)} por {parametro.updated_by}
          </div>
          {error ? <div className="rojo" style={{ fontSize: 11.5, marginTop: 3 }}>{error}</div> : null}
        </div>

        <div className="fila" style={{ gap: 8 }}>
          <input
            className="control num"
            inputMode="numeric"
            value={texto}
            onChange={(evento) => setTexto(evento.target.value)}
            style={{ width: 110 }}
          />
          <span className="tenue" style={{ minWidth: 44 }}>{presentacion?.unidad ?? 'valor'}</span>
          <Boton
            chico
            variante={cambiado ? 'principal' : 'normal'}
            disabled={!cambiado || guardando}
            onClick={() => void guardar()}
          >
            {guardando ? 'Guardando…' : 'Guardar'}
          </Boton>
        </div>
      </div>
    </li>
  )
}
