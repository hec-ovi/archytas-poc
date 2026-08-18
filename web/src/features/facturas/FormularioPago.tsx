import { useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { pesos } from '../../lib/format'
import { Boton } from '../../ui/Boton'
import { Campo } from '../../ui/Campo'
import type { Factura } from '../../lib/types'

const hoy = () => new Date().toISOString().slice(0, 10)

/** Register a payment on account. The api refuses anything over the balance. */
export function FormularioPago({ factura, onListo }: { factura: Factura; onListo: () => void }) {
  const [monto, setMonto] = useState('')
  const [dia, setDia] = useState(hoy())
  const [referencia, setReferencia] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  const saldado = factura.balance_cents <= 0
  const centavos = Math.round(Number(monto.replace(',', '.')) * 100)

  const enviar = async (evento: React.FormEvent) => {
    evento.preventDefault()
    setError(null)
    if (!Number.isFinite(centavos) || centavos <= 0) {
      setError('Escribí un monto en pesos, por ejemplo 125000')
      return
    }
    setGuardando(true)
    try {
      await api.facturas.pagar(factura.id, {
        monto_centavos: centavos,
        fecha: dia,
        referencia: referencia.trim(),
      })
      setMonto('')
      setReferencia('')
      onListo()
    } catch (problema) {
      setError(mensajeDeError(problema))
    } finally {
      setGuardando(false)
    }
  }

  if (saldado) return <div className="aviso exito">Esta factura ya está saldada. No queda saldo para pagar.</div>

  return (
    <form className="formulario" onSubmit={enviar}>
      <div className="grilla g3">
        <Campo etiqueta="Monto en pesos" ayuda={`Saldo pendiente: ${pesos(factura.balance_cents)}`}>
          <input
            inputMode="decimal"
            value={monto}
            onChange={(evento) => setMonto(evento.target.value)}
            placeholder="0"
          />
        </Campo>
        <Campo etiqueta="Fecha del pago">
          <input type="date" value={dia} onChange={(evento) => setDia(evento.target.value)} />
        </Campo>
        <Campo etiqueta="Referencia" ayuda="Número de transferencia o recibo, si lo tenés">
          <input value={referencia} onChange={(evento) => setReferencia(evento.target.value)} placeholder="Opcional" />
        </Campo>
      </div>
      {error ? <div className="aviso error">{error}</div> : null}
      <div className="acciones">
        <Boton type="submit" variante="principal" disabled={guardando}>
          {guardando ? 'Registrando…' : 'Registrar pago'}
        </Boton>
        <button
          type="button"
          className="boton plano"
          onClick={() => setMonto(String(Math.round(factura.balance_cents / 100)))}
        >
          Poner el saldo completo
        </button>
      </div>
    </form>
  )
}
