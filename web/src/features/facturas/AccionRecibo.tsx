import { useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { fecha } from '../../lib/format'
import { Boton } from '../../ui/Boton'
import type { Factura, Recibo } from '../../lib/types'

interface Props {
  factura: Factura
  recibo: Recibo | null
  onListo: () => void
}

/** Issue the receipt. The api only accepts it up to the due date. */
export function AccionRecibo({ factura, recibo, onListo }: Props) {
  const [error, setError] = useState<string | null>(null)
  const [emitiendo, setEmitiendo] = useState(false)

  const emitir = async () => {
    setError(null)
    setEmitiendo(true)
    try {
      await api.facturas.emitirRecibo(factura.id)
      onListo()
    } catch (problema) {
      setError(mensajeDeError(problema))
    } finally {
      setEmitiendo(false)
    }
  }

  if (recibo) {
    return (
      <div className="pila">
        <div className="aviso exito">
          Recibo <strong>{recibo.number}</strong> emitido el {fecha(recibo.issued_on)} por {recibo.issued_by}.
        </div>
        {typeof recibo.extra?.origen === 'string' ? <div className="tenue">{recibo.extra.origen}</div> : null}
      </div>
    )
  }

  return (
    <div className="pila">
      <div className="aviso">
        Esta factura no tiene comprobante de recepción emitido. El portal lo acepta hasta la fecha de
        vencimiento ({fecha(factura.due_on)}).
      </div>
      {error ? <div className="aviso error">{error}</div> : null}
      <div className="fila">
        <Boton variante="principal" onClick={() => void emitir()} disabled={emitiendo}>
          {emitiendo ? 'Emitiendo…' : 'Emitir recibo'}
        </Boton>
      </div>
    </div>
  )
}
