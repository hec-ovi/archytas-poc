import { Boton } from '../ui/Boton'
import { useSesion } from './sesion'

/** The api is not answering. Saying so beats pretending the session expired. */
export function SinServidor({ mensaje }: { mensaje: string }) {
  const { reintentar, verificando } = useSesion()
  return (
    <div style={{ maxWidth: 520, margin: '12vh auto', padding: '0 24px' }}>
      <h1 className="titulo-pagina">No se puede conectar con el sistema</h1>
      <div className="subtitulo-pagina" style={{ marginBottom: 16 }}>
        El servidor de Cordillera no está respondiendo. Si recién lo prendieron, esperá unos
        segundos y probá de nuevo.
      </div>
      <div className="aviso" style={{ marginBottom: 16 }}>{mensaje}</div>
      <Boton variante="principal" onClick={reintentar} disabled={verificando}>
        {verificando ? 'Probando…' : 'Probar de nuevo'}
      </Boton>
    </div>
  )
}
