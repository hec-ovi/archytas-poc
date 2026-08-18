import { useMemo, useState } from 'react'
import { api } from '../../lib/api'
import { useRecurso } from '../../lib/useRecurso'
import { useEventoVivo } from '../../lib/useCanalVivo'
import { pesos } from '../../lib/format'
import { Pagina } from '../../app/Pagina'
import { Panel } from '../../ui/Panel'
import { Metrica } from '../../ui/Metrica'
import { Bloque } from '../../ui/Estado'
import { FiltrosFacturas, type EstadoFiltros } from './FiltrosFacturas'
import { TablaFacturas } from './TablaFacturas'
import { ModalFactura } from './ModalFactura'

const VACIO: EstadoFiltros = { estado: '', proveedor: '', soloSinRecibo: false, busqueda: '' }

export function PantallaFacturas() {
  const [filtros, setFiltros] = useState<EstadoFiltros>(VACIO)
  const [abierta, setAbierta] = useState<number | null>(null)

  const listado = useRecurso(
    () => api.facturas.listar({
      estado: filtros.estado || undefined,
      proveedor: filtros.proveedor ? Number(filtros.proveedor) : undefined,
    }),
    [filtros.estado, filtros.proveedor],
  )
  const proveedores = useRecurso(() => api.proveedores.listar(), [])

  useEventoVivo('factura-actualizada', () => listado.recargar())
  useEventoVivo('recibo-emitido', () => listado.recargar())

  const filtradas = useMemo(() => {
    const texto = filtros.busqueda.trim().toLowerCase()
    return (listado.datos?.facturas ?? []).filter((factura) => {
      if (filtros.soloSinRecibo && factura.has_receipt) return false
      if (!texto) return true
      return `${factura.number} ${factura.supplier_name ?? ''}`.toLowerCase().includes(texto)
    })
  }, [listado.datos, filtros.busqueda, filtros.soloSinRecibo])

  const totales = useMemo(() => ({
    monto: filtradas.reduce((suma, f) => suma + f.amount_cents, 0),
    saldo: filtradas.reduce((suma, f) => suma + f.balance_cents, 0),
    sinRecibo: filtradas.filter((f) => !f.has_receipt).length,
  }), [filtradas])

  return (
    <Pagina
      titulo="Facturas"
      subtitulo="Lo que compramos, lo que ya pagamos y lo que falta. Tocá una fila para pagar, emitir el recibo o ajustar el monto."
    >
      <div className="pila">
        <div className="grilla g4">
          <Metrica
            rotulo="Impagas"
            valor={listado.datos?.resumen.impaga ?? '-'}
            pie="sin ningún pago registrado"
            tono="urgente"
          />
          <Metrica
            rotulo="Pago parcial"
            valor={listado.datos?.resumen.parcial ?? '-'}
            pie="tienen algo pago y les queda saldo"
            tono="aviso"
          />
          <Metrica rotulo="Saldadas" valor={listado.datos?.resumen.saldada ?? '-'} pie="no deben nada" />
          <Metrica
            rotulo="Saldo del filtro"
            valor={pesos(totales.saldo)}
            pie={`sobre ${pesos(totales.monto)} facturados`}
            tono="calma"
          />
        </div>

        <Panel
          titulo="Listado"
          nota={`${filtradas.length} facturas · ${totales.sinRecibo} sin recibo`}
        >
          <FiltrosFacturas
            filtros={filtros}
            onCambiar={setFiltros}
            proveedores={proveedores.datos?.proveedores ?? []}
            resumen={listado.datos?.resumen ?? null}
          />
        </Panel>

        <Panel titulo="Facturas" nota={listado.cargando ? 'actualizando…' : undefined} pegado>
          <Bloque recurso={listado} que="Cargando las facturas">
            {() => <TablaFacturas facturas={filtradas} onAbrir={setAbierta} seleccionada={abierta} alto={560} />}
          </Bloque>
        </Panel>
      </div>

      {abierta === null ? null : (
        <ModalFactura id={abierta} onCerrar={() => setAbierta(null)} onCambio={() => listado.recargar()} />
      )}
    </Pagina>
  )
}
