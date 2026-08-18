import { useCallback, useMemo, useState } from 'react'
import { api } from '../../lib/api'
import { mensajeDeError } from '../../lib/errors'
import { useRecurso } from '../../lib/useRecurso'
import { useEventoVivo } from '../../lib/useCanalVivo'
import { nombreMes, pesos } from '../../lib/format'
import { Pagina } from '../../app/Pagina'
import { Boton } from '../../ui/Boton'
import { Panel } from '../../ui/Panel'
import { Bloque } from '../../ui/Estado'
import { ModalFactura } from '../facturas/ModalFactura'
import { GrillaMes } from './GrillaMes'
import { PanelDia } from './PanelDia'
import { FormularioEvento } from './FormularioEvento'
import { armarGrilla, correrMes, hoyISO, mesDeHoy, type Mes } from './mes'
import type { EventoCalendario } from '../../lib/types'
import './calendario.css'

export function PantallaCalendario() {
  const [mes, setMes] = useState<Mes>(mesDeHoy)
  const [diaElegido, setDiaElegido] = useState<string>(hoyISO)
  const [diaEncima, setDiaEncima] = useState<string | null>(null)
  const [arrastrado, setArrastrado] = useState<number | null>(null)
  const [factura, setFactura] = useState<number | null>(null)
  const [agregando, setAgregando] = useState(false)
  const [problema, setProblema] = useState<string | null>(null)

  const rango = useMemo(() => {
    const casillas = armarGrilla(mes)
    return { desde: casillas[0].fecha, hasta: casillas[casillas.length - 1].fecha }
  }, [mes])

  const recurso = useRecurso(() => api.calendario.listar(rango.desde, rango.hasta), [rango.desde, rango.hasta])
  const proveedores = useRecurso(() => api.proveedores.listar(), [])
  const eventos = recurso.datos?.eventos ?? []

  const enRango = useCallback(
    (dia: string) => dia >= rango.desde && dia <= rango.hasta,
    [rango.desde, rango.hasta],
  )

  /** The live channel is the only writer here besides this page's own actions. */
  const aplicar = useCallback((accion: string, evento: EventoCalendario) => {
    recurso.fijar((actual) => {
      if (!actual) return actual
      const sinEse = actual.eventos.filter((item) => item.id !== evento.id)
      const siguiente = accion === 'baja' || !enRango(evento.on_date) ? sinEse : [...sinEse, evento]
      return { ...actual, eventos: siguiente }
    })
  }, [recurso, enRango])

  useEventoVivo('calendario-cambio', (datos) => {
    const evento = datos.evento as EventoCalendario | undefined
    if (!evento) return
    aplicar(String(datos.accion), evento)
  })
  useEventoVivo('factura-actualizada', () => recurso.recargar())
  useEventoVivo('recibo-emitido', () => recurso.recargar())

  const mover = async (id: number, destino: string) => {
    const original = eventos.find((evento) => evento.id === id)
    if (!original || original.on_date === destino) return
    setProblema(null)
    aplicar('movido', { ...original, on_date: destino, moved_from: original.on_date })
    try {
      const { evento } = await api.calendario.mover(id, destino)
      aplicar('movido', evento)
    } catch (error) {
      aplicar('movido', original)
      setProblema(mensajeDeError(error))
    }
  }

  const borrar = async (evento: EventoCalendario) => {
    setProblema(null)
    try {
      await api.calendario.borrar(evento.id)
      aplicar('baja', evento)
    } catch (error) {
      setProblema(mensajeDeError(error))
    }
  }

  const delDia = eventos.filter((evento) => evento.on_date === diaElegido)
  const totalMes = eventos
    .filter((evento) => evento.on_date.startsWith(`${mes.anio}-${String(mes.mes).padStart(2, '0')}`))
    .reduce((suma, evento) => suma + (evento.balance_cents ?? evento.amount_cents ?? 0), 0)

  return (
    <Pagina
      titulo="Calendario de vencimientos"
      subtitulo="Arrastrá un vencimiento a otro día para moverlo. Lo que cambie otra persona aparece acá solo."
      acciones={
        <>
          <Boton onClick={() => setMes(correrMes(mes, -1))}>‹ Mes anterior</Boton>
          <Boton onClick={() => { setMes(mesDeHoy()); setDiaElegido(hoyISO()) }}>Hoy</Boton>
          <Boton onClick={() => setMes(correrMes(mes, 1))}>Mes siguiente ›</Boton>
          <Boton variante="principal" onClick={() => setAgregando(true)}>Agregar vencimiento</Boton>
        </>
      }
    >
      <div className="pila">
        {problema ? <div className="aviso error">{problema}</div> : null}

        <div className="grilla g-2-1">
          <Panel
            titulo={`${nombreMes(mes.mes - 1)} ${mes.anio}`}
            nota={`${eventos.length} vencimientos en pantalla · ${pesos(totalMes)} en el mes`}
            pegado
          >
            <Bloque recurso={recurso} que="Cargando el calendario">
              {() => (
                <GrillaMes
                  mes={mes}
                  eventos={eventos}
                  diaElegido={diaElegido}
                  diaEncima={diaEncima}
                  arrastrado={arrastrado}
                  onElegirDia={setDiaElegido}
                  onAbrirEvento={(evento) => {
                    setDiaElegido(evento.on_date)
                    if (evento.invoice_id) setFactura(evento.invoice_id)
                  }}
                  onArrastrar={setArrastrado}
                  onSoltarChip={() => { setArrastrado(null); setDiaEncima(null) }}
                  onEntrar={setDiaEncima}
                  onSoltarEnDia={(dia) => {
                    if (arrastrado !== null) void mover(arrastrado, dia)
                    setArrastrado(null)
                  }}
                />
              )}
            </Bloque>
          </Panel>

          <div className="pila">
            <PanelDia
              dia={diaElegido}
              eventos={delDia}
              onAbrirEvento={(evento) => { if (evento.invoice_id) setFactura(evento.invoice_id) }}
              onBorrar={(evento) => void borrar(evento)}
              onAgregar={() => setAgregando(true)}
            />

            <Panel titulo="Cómo leer el calendario">
              <div className="pila" style={{ gap: 10 }}>
                <div className="cal-referencias">
                  <span><span className="muestra" style={{ borderLeftColor: 'var(--rojo)', background: 'var(--rojo-fondo)' }} />Impaga</span>
                  <span><span className="muestra" style={{ borderLeftColor: 'var(--ambar)', background: 'var(--ambar-fondo)' }} />Pago parcial</span>
                  <span><span className="muestra" style={{ borderLeftColor: 'var(--verde)', background: 'var(--verde-fondo)' }} />Saldada</span>
                  <span><span className="muestra" style={{ borderLeftColor: 'var(--acento)', background: 'var(--acento-tenue)' }} />Agregado a mano</span>
                </div>
                <div className="fila" style={{ gap: 6 }}>
                  <span className="marca-recibo" style={{ display: 'inline-block', width: 8, height: 8, border: '1.5px dashed var(--violeta)' }} />
                  <span>El cuadrado punteado marca las facturas que todavía no tienen recibo emitido.</span>
                </div>
                <div className="tenue">
                  Cada chip muestra el proveedor y el saldo. Tocá un día para ver el detalle, y arrastrá un chip
                  a otro día para reprogramarlo: queda registrado de dónde venía.
                </div>
              </div>
            </Panel>
          </div>
        </div>
      </div>

      {agregando ? (
        <FormularioEvento
          fechaInicial={diaElegido}
          proveedores={proveedores.datos?.proveedores ?? []}
          onCerrar={() => setAgregando(false)}
          onCreado={recurso.recargar}
        />
      ) : null}

      {factura === null ? null : (
        <ModalFactura id={factura} onCerrar={() => setFactura(null)} onCambio={recurso.recargar} />
      )}
    </Pagina>
  )
}