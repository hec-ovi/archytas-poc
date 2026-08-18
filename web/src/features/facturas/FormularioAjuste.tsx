import { useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { fecha, pesos } from '../../lib/format'
import { Boton } from '../../ui/Boton'
import { Campo } from '../../ui/Campo'
import type { Ajuste, Factura } from '../../lib/types'

interface Props {
  factura: Factura
  ajustes: Ajuste[]
  onListo: () => void
}

/** Change the amount of an invoice. The reason is required and stays on the record. */
export function FormularioAjuste({ factura, ajustes, onListo }: Props) {
  const [monto, setMonto] = useState(String(Math.round(factura.amount_cents / 100)))
  const [motivo, setMotivo] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  const enviar = async (evento: React.FormEvent) => {
    evento.preventDefault()
    setError(null)
    const centavos = Math.round(Number(monto.replace(',', '.')) * 100)
    if (!Number.isFinite(centavos) || centavos < 0) {
      setError('Escribí el monto nuevo en pesos')
      return
    }
    if (motivo.trim().length < 3) {
      setError('Escribí por qué se ajusta. Queda guardado con tu nombre.')
      return
    }
    setGuardando(true)
    try {
      await api.facturas.ajustar(factura.id, { monto_centavos: centavos, motivo: motivo.trim() })
      setMotivo('')
      onListo()
    } catch (problema) {
      setError(mensajeDeError(problema))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="pila">
      <form className="formulario" onSubmit={enviar}>
        <div className="grilla g2">
          <Campo etiqueta="Monto nuevo en pesos" ayuda={`Hoy figura ${pesos(factura.amount_cents)}`}>
            <input inputMode="decimal" value={monto} onChange={(evento) => setMonto(evento.target.value)} />
          </Campo>
          <Campo etiqueta="Motivo del ajuste" ayuda="Se guarda quién lo hizo y cuándo">
            <input
              value={motivo}
              onChange={(evento) => setMotivo(evento.target.value)}
              placeholder="Nota de crédito, error de carga, diferencia de flete…"
            />
          </Campo>
        </div>
        {error ? <div className="aviso error">{error}</div> : null}
        <div className="acciones">
          <Boton type="submit" variante="principal" disabled={guardando}>
            {guardando ? 'Ajustando…' : 'Ajustar el monto'}
          </Boton>
        </div>
      </form>

      {ajustes.length ? (
        <div>
          <div className="rotulo" style={{ marginBottom: 6 }}>Ajustes anteriores</div>
          <table className="tabla">
            <thead>
              <tr>
                <th>Cuándo</th>
                <th>Quién</th>
                <th className="num">De</th>
                <th className="num">A</th>
                <th className="ancho">Motivo</th>
              </tr>
            </thead>
            <tbody>
              {ajustes.map((ajuste, indice) => (
                <tr key={`${ajuste.cuando}-${indice}`}>
                  <td className="num">{fecha(ajuste.cuando)}</td>
                  <td>{ajuste.por}</td>
                  <td className="num tenue">{pesos(ajuste.de)}</td>
                  <td className="num fuerte">{pesos(ajuste.a)}</td>
                  <td className="ancho">{ajuste.motivo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
