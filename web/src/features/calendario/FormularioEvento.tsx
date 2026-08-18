import { useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { Boton } from '../../ui/Boton'
import { Campo } from '../../ui/Campo'
import { Modal } from '../../ui/Modal'
import type { PosicionProveedor } from '../../lib/types'

interface Props {
  fechaInicial: string
  proveedores: PosicionProveedor[]
  onCerrar: () => void
  onCreado: () => void
}

/** Add a due date by hand: the ones that never came through the portal. */
export function FormularioEvento({ fechaInicial, proveedores, onCerrar, onCreado }: Props) {
  const [titulo, setTitulo] = useState('')
  const [dia, setDia] = useState(fechaInicial)
  const [monto, setMonto] = useState('')
  const [proveedor, setProveedor] = useState('')
  const [nota, setNota] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  const enviar = async (evento: React.FormEvent) => {
    evento.preventDefault()
    setError(null)
    if (!titulo.trim()) {
      setError('Poné un título, por ejemplo "Vence anticipo Aceros Belgrano"')
      return
    }
    const centavos = monto.trim() ? Math.round(Number(monto.replace(',', '.')) * 100) : null
    if (centavos !== null && !Number.isFinite(centavos)) {
      setError('El monto tiene que ser un número en pesos')
      return
    }
    setGuardando(true)
    try {
      await api.calendario.agregar({
        titulo: titulo.trim(),
        fecha: dia,
        nota: nota.trim(),
        monto_centavos: centavos,
        proveedor_id: proveedor ? Number(proveedor) : null,
      })
      onCreado()
      onCerrar()
    } catch (problema) {
      setError(mensajeDeError(problema))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <Modal titulo={<strong>Agregar un vencimiento a mano</strong>} onCerrar={onCerrar} angosto>
      <form className="formulario" onSubmit={enviar}>
        <Campo etiqueta="Título" ayuda="Lo que se lee en el calendario">
          <input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Vence anticipo…" autoFocus />
        </Campo>
        <div className="grilla g2">
          <Campo etiqueta="Fecha">
            <input type="date" value={dia} onChange={(e) => setDia(e.target.value)} />
          </Campo>
          <Campo etiqueta="Monto en pesos" ayuda="Opcional">
            <input inputMode="decimal" value={monto} onChange={(e) => setMonto(e.target.value)} placeholder="0" />
          </Campo>
        </div>
        <Campo etiqueta="Proveedor" ayuda="Opcional">
          <select value={proveedor} onChange={(e) => setProveedor(e.target.value)}>
            <option value="">Sin proveedor</option>
            {proveedores.map((item) => (
              <option key={item.supplier_id} value={String(item.supplier_id)}>{item.name}</option>
            ))}
          </select>
        </Campo>
        <Campo etiqueta="Nota" ayuda="Opcional">
          <input value={nota} onChange={(e) => setNota(e.target.value)} placeholder="Lo que haga falta recordar" />
        </Campo>
        {error ? <div className="aviso error">{error}</div> : null}
        <div className="acciones">
          <Boton type="submit" variante="principal" disabled={guardando}>
            {guardando ? 'Agregando…' : 'Agregar al calendario'}
          </Boton>
          <Boton onClick={onCerrar}>Cancelar</Boton>
        </div>
      </form>
    </Modal>
  )
}
