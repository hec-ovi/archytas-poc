import { fechaHora, numero, pesos } from '../../lib/format'
import { Boton } from '../../ui/Boton'
import { Chapa } from '../../ui/Chapa'
import { DatosCrudos } from './DatosCrudos'
import type { CandidatoRevision, PendienteRevision, VentaExcluida } from '../../lib/types'
import { armarDecision, huellaDeFila } from './decision'

const TIPO: Record<string, string> = {
  'venta-duplicada': 'Venta duplicada',
  'venta-rota': 'Venta con datos rotos',
  proveedor: 'Proveedor sin identificar',
  rubro: 'Rubro sin identificar',
}

interface Props {
  pendiente: PendienteRevision
  excluidas: VentaExcluida[] | null
  trabajando: boolean
  onResolver: (decision: Record<string, unknown>) => void
  onDescartar: () => void
}

export function TarjetaPendiente({ pendiente, excluidas, trabajando, onResolver, onDescartar }: Props) {
  const candidatos: CandidatoRevision[] = Array.isArray(pendiente.candidates) ? pendiente.candidates : []
  const filas = (pendiente.raw.filas as Record<string, string>[] | undefined) ?? []

  return (
    <article className="rev-tarjeta">
      <div className="rev-cuerpo">
        <div className="fila" style={{ justifyContent: 'space-between' }}>
          <span className="fila" style={{ gap: 8 }}>
            <Chapa tono={pendiente.kind === 'venta-rota' ? 'impaga' : 'parcial'}>
              {TIPO[pendiente.kind] ?? pendiente.kind}
            </Chapa>
            <span className="rev-titulo">{pendiente.title}</span>
          </span>
          <span className="tenue" style={{ fontSize: 11.5 }}>{fechaHora(pendiente.created_at)}</span>
        </div>

        <div className="rev-detalle">{pendiente.detail}</div>

        {filas.length ? (
          <div className="rev-filas">
            <div className="rotulo" style={{ marginBottom: 4 }}>Lo que llegó</div>
            <table className="tabla">
              <thead>
                <tr>
                  {Object.keys(filas[0]).map((clave) => <th key={clave}>{clave}</th>)}
                </tr>
              </thead>
              <tbody>
                {filas.map((fila, indice) => (
                  <tr key={indice}>
                    {Object.keys(filas[0]).map((clave) => <td key={clave}>{fila[clave]}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div>
            <div className="rotulo" style={{ marginBottom: 4 }}>Lo que llegó</div>
            <DatosCrudos datos={pendiente.raw} />
          </div>
        )}
      </div>

      <div className="rev-lado">
        <div className="rotulo">Lo que sospecha el sistema</div>

        {candidatos.length === 0 ? (
          <div className="tenue">
            No hay una sugerencia con respaldo. El sistema prefiere no adivinar: resolvelo vos o descartalo.
          </div>
        ) : (
          candidatos.map((candidato, indice) => {
            const eleccion = armarDecision(pendiente, candidato, excluidas)
            const sinHuella = pendiente.kind === 'venta-duplicada' && !huellaDeFila(candidato.fila, excluidas)
            return (
              <button
                key={indice}
                className="rev-candidato"
                disabled={trabajando || sinHuella}
                onClick={() => onResolver(eleccion.decision)}
                title={sinHuella ? 'Para aplicar esta elección hace falta acceso a la sección Ventas' : undefined}
              >
                <span className="valor">
                  {typeof candidato.valor === 'number' ? pesos(candidato.valor) : candidato.valor}
                </span>
                <span className="confianza">
                  Confianza {numero(Math.round((candidato.puntaje ?? 0) * 100))}%
                  {candidato.nota ? ` · ${candidato.nota}` : ''}
                </span>
              </button>
            )
          })
        )}

        <div className="fila" style={{ marginTop: 'auto', gap: 6 }}>
          <Boton
            chico
            disabled={trabajando}
            onClick={() => onResolver({ revisado_a_mano: true })}
          >
            Marcar revisado
          </Boton>
          <Boton chico variante="peligro" disabled={trabajando} onClick={onDescartar}>
            Descartar
          </Boton>
        </div>
      </div>
    </article>
  )
}
