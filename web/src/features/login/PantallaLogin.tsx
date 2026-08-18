import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Boton } from '../../ui/Boton'
import { Campo } from '../../ui/Campo'
import { mensajeDeError } from '../../lib/errors'
import { useSesion } from '../../app/sesion'
import { primeraRuta } from '../../app/secciones'
import { USUARIOS } from './usuarios'
import './login.css'

export function PantallaLogin() {
  const { sesion, verificando, sinServidor, entrar } = useSesion()
  const navegar = useNavigate()
  const lugar = useLocation() as { state?: { desde?: string } }
  const [usuario, setUsuario] = useState('duenio')
  const [clave, setClave] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [entrando, setEntrando] = useState(false)

  if (verificando) return <div className="cargando" style={{ paddingTop: 120 }}>Verificando la sesión</div>
  if (sesion) return <Navigate to={primeraRuta(sesion.secciones)} replace />

  const enviar = async (evento: React.FormEvent) => {
    evento.preventDefault()
    setEntrando(true)
    setError(null)
    try {
      await entrar(usuario, clave)
      navegar(lugar.state?.desde ?? '/tablero', { replace: true })
    } catch (problema) {
      setError(mensajeDeError(problema))
    } finally {
      setEntrando(false)
    }
  }

  return (
    <div className="entrada">
      <section className="entrada-lado">
        <h1><span>Ferretería Industrial</span>Cordillera</h1>
        <p>
          Todo lo que hoy está repartido entre el portal viejo, el Excel y los mails, en una sola
          pantalla que se entiende de un vistazo.
        </p>
        <ul>
          <li>Qué vence esta semana y a quién le debemos</li>
          <li>Qué facturas todavía no tienen recibo emitido</li>
          <li>Qué ventas quedaron afuera de los totales y por qué</li>
          <li>Qué órdenes de compra quedaron olvidadas</li>
        </ul>
      </section>

      <form className="entrada-caja" onSubmit={enviar}>
        <div>
          <h2 className="titulo-pagina">Entrar</h2>
          <div className="subtitulo-pagina">Elegí tu usuario y escribí la clave.</div>
        </div>

        <div className="entrada-usuarios">
          {USUARIOS.map((opcion) => (
            <button
              key={opcion.usuario}
              type="button"
              className={opcion.usuario === usuario ? 'entrada-usuario elegido' : 'entrada-usuario'}
              onClick={() => setUsuario(opcion.usuario)}
            >
              <strong>{opcion.nombre}</strong>
              <span>{opcion.detalle}</span>
            </button>
          ))}
        </div>

        <Campo etiqueta="Clave">
          <input
            type="password"
            value={clave}
            autoFocus
            autoComplete="current-password"
            onChange={(evento) => setClave(evento.target.value)}
            placeholder="Tu clave"
          />
        </Campo>

        {error ?? sinServidor ? <div className="aviso error" role="alert">{error ?? sinServidor}</div> : null}

        <Boton type="submit" variante="principal" disabled={entrando || !clave}>
          {entrando ? 'Entrando…' : `Entrar como ${USUARIOS.find((u) => u.usuario === usuario)?.nombre}`}
        </Boton>
      </form>
    </div>
  )
}
