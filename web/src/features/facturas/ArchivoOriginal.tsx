import { useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { Boton } from '../../ui/Boton'
import { ChapaOrigen } from '../../ui/Chapa'

/**
 * The invoice as the supplier sent it. The api goes to get it from the portal at that moment,
 * so the tab is opened on the click and only then filled: a blocked popup would lose it.
 */
export function ArchivoOriginal({ id, origen }: { id: number; origen: string | null | undefined }) {
  const [buscando, setBuscando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const abrir = async () => {
    setError(null)
    setBuscando(true)
    const ventana = window.open('', '_blank')
    try {
      const archivo = await api.facturas.archivo(id)
      const url = URL.createObjectURL(archivo)
      if (ventana) {
        ventana.location.href = url
      } else {
        setError('El navegador bloqueó la ventana nueva. Permití las ventanas emergentes para este sitio.')
      }
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch (problema) {
      ventana?.close()
      setError(mensajeDeError(problema))
    } finally {
      setBuscando(false)
    }
  }

  return (
    <div className="pila" style={{ gap: 6 }}>
      <div className="fila" style={{ gap: 10 }}>
        <span className="rotulo">Archivo original</span>
        <ChapaOrigen origen={origen} />
        <Boton chico onClick={() => void abrir()} disabled={buscando}>
          {buscando ? 'Bajando del portal…' : 'Ver el original'}
        </Boton>
      </div>
      {error ? <div className="aviso error">{error}</div> : null}
    </div>
  )
}
