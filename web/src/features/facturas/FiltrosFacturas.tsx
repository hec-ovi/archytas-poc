import { Campo } from '../../ui/Campo'
import type { PosicionProveedor, ResumenPagos } from '../../lib/types'

export interface EstadoFiltros {
  estado: string
  proveedor: string
  soloSinRecibo: boolean
  busqueda: string
}

interface Props {
  filtros: EstadoFiltros
  onCambiar: (filtros: EstadoFiltros) => void
  proveedores: PosicionProveedor[]
  resumen: ResumenPagos | null
}

export function FiltrosFacturas({ filtros, onCambiar, proveedores, resumen }: Props) {
  const set = (parche: Partial<EstadoFiltros>) => onCambiar({ ...filtros, ...parche })

  return (
    <div className="filtros">
      <Campo etiqueta="Estado de pago">
        <select value={filtros.estado} onChange={(evento) => set({ estado: evento.target.value })}>
          <option value="">Todas{resumen ? ` (${resumen.impaga + resumen.parcial + resumen.saldada})` : ''}</option>
          <option value="impaga">Impagas{resumen ? ` (${resumen.impaga})` : ''}</option>
          <option value="parcial">Pago parcial{resumen ? ` (${resumen.parcial})` : ''}</option>
          <option value="saldada">Saldadas{resumen ? ` (${resumen.saldada})` : ''}</option>
        </select>
      </Campo>

      <Campo etiqueta="Proveedor">
        <select value={filtros.proveedor} onChange={(evento) => set({ proveedor: evento.target.value })}>
          <option value="">Todos</option>
          {proveedores.map((proveedor) => (
            <option key={proveedor.supplier_id} value={String(proveedor.supplier_id)}>
              {proveedor.name}
            </option>
          ))}
        </select>
      </Campo>

      <Campo etiqueta="Buscar" className="crecer">
        <input
          value={filtros.busqueda}
          onChange={(evento) => set({ busqueda: evento.target.value })}
          placeholder="Número de factura o proveedor"
        />
      </Campo>

      <label className="fila" style={{ gap: 6, paddingBottom: 6 }}>
        <input
          type="checkbox"
          checked={filtros.soloSinRecibo}
          onChange={(evento) => set({ soloSinRecibo: evento.target.checked })}
          style={{ width: 'auto' }}
        />
        <span>Solo las que no tienen recibo</span>
      </label>
    </div>
  )
}
