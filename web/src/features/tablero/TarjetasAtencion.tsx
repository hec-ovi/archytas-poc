import { Metrica } from '../../ui/Metrica'
import { numero, pesos } from '../../lib/format'
import type { Tablero } from '../../lib/types'

/** What is wrong today, before any number anybody would call good news. */
export function TarjetasAtencion({ datos }: { datos: Tablero }) {
  const porVencer = datos.vencen_pronto.reduce((suma, f) => suma + f.balance_cents, 0)
  const deuda = datos.deuda_por_proveedor.reduce((suma, p) => suma + p.owed_cents, 0)
  const excluidas = datos.salud_ventas.excluidas_total
  const excluidasCentavos = Object.values(datos.salud_ventas.excluidas).reduce((suma, e) => suma + e.cents, 0)

  return (
    <div className="grilla g4">
      <Metrica
        rotulo="Vencen pronto"
        valor={numero(datos.vencen_pronto.length)}
        pie={`${pesos(porVencer)} por pagar`}
        tono="urgente"
        a="/calendario"
      />
      <Metrica
        rotulo="Sin recibo emitido"
        valor={numero(datos.sin_recibo.length)}
        pie="facturas recibidas sin comprobante"
        tono="urgente"
        a="/facturas"
      />
      <Metrica
        rotulo="Órdenes olvidadas"
        valor={numero(datos.ordenes_olvidadas.length)}
        pie="abiertas hace demasiado"
        tono="aviso"
        a="/ordenes"
      />
      <Metrica
        rotulo="Esperan tu decisión"
        valor={numero(datos.pendientes_revision)}
        pie="el sistema no quiso adivinar"
        tono="aviso"
        a="/revision"
      />
      <Metrica
        rotulo="Deuda con proveedores"
        valor={pesos(deuda)}
        pie={`${datos.deuda_por_proveedor.filter((p) => p.owed_cents > 0).length} proveedores con saldo`}
        tono="calma"
        a="/proveedores"
      />
      <Metrica
        rotulo="Ventas fuera del total"
        valor={numero(excluidas)}
        pie={`${pesos(excluidasCentavos)} sin sumar, con motivo`}
        tono="aviso"
        a="/ventas"
      />
      <Metrica
        rotulo="Mensajes abiertos"
        valor={numero(datos.mensajes_abiertos)}
        pie="reclamos y avisos sin resolver"
        a="/mensajes"
      />
      <Metrica
        rotulo="Facturas impagas"
        valor={numero(datos.estado_pagos.impaga)}
        pie={`${datos.estado_pagos.parcial} con pago parcial · ${datos.estado_pagos.saldada} saldadas`}
        a="/facturas"
      />
    </div>
  )
}
