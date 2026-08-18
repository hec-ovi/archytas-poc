import { Metrica } from '../../ui/Metrica'
import { numero, pesos } from '../../lib/format'
import { useSesion } from '../../app/sesion'
import type { Seccion, Tablero } from '../../lib/types'

/** What is wrong today, before any number anybody would call good news. */
export function TarjetasAtencion({ datos }: { datos: Tablero }) {
  const { puede } = useSesion()
  const porVencer = datos.vencen_pronto.reduce((suma, f) => suma + f.balance_cents, 0)
  const deuda = datos.deuda_por_proveedor.reduce((suma, p) => suma + p.owed_cents, 0)
  const excluidasCentavos = Object.values(datos.salud_ventas.excluidas).reduce((suma, e) => suma + e.cents, 0)

  // a card only links where the person is allowed to go
  const tarjetas: { seccion: Seccion; nodo: React.ReactNode }[] = [
    {
      seccion: 'calendario',
      nodo: <Metrica
        rotulo="Vencen pronto"
        valor={numero(datos.vencen_pronto.length)}
        pie={`${pesos(porVencer)} por pagar`}
        tono="urgente"
        a={puede('calendario') ? '/calendario' : undefined}
      />,
    },
    {
      seccion: 'facturas',
      nodo: <Metrica
        rotulo="Sin recibo emitido"
        valor={numero(datos.sin_recibo.length)}
        pie="facturas recibidas sin comprobante"
        tono="urgente"
        a={puede('facturas') ? '/facturas' : undefined}
      />,
    },
    {
      seccion: 'ordenes',
      nodo: <Metrica
        rotulo="Órdenes olvidadas"
        valor={numero(datos.ordenes_olvidadas.length)}
        pie="abiertas hace demasiado"
        tono="aviso"
        a={puede('ordenes') ? '/ordenes' : undefined}
      />,
    },
    {
      seccion: 'revision',
      nodo: <Metrica
        rotulo="Esperan tu decisión"
        valor={numero(datos.pendientes_revision)}
        pie="el sistema no quiso adivinar"
        tono="aviso"
        a={puede('revision') ? '/revision' : undefined}
      />,
    },
    {
      seccion: 'proveedores',
      nodo: <Metrica
        rotulo="Deuda con proveedores"
        valor={pesos(deuda)}
        pie={`${datos.deuda_por_proveedor.filter((p) => p.owed_cents > 0).length} proveedores con saldo`}
        tono="calma"
        a={puede('proveedores') ? '/proveedores' : undefined}
      />,
    },
    {
      seccion: 'ventas',
      nodo: <Metrica
        rotulo="Ventas fuera del total"
        valor={numero(datos.salud_ventas.excluidas_total)}
        pie={`${pesos(excluidasCentavos)} sin sumar, con motivo`}
        tono="aviso"
        a={puede('ventas') ? '/ventas' : undefined}
      />,
    },
    {
      seccion: 'mensajes',
      nodo: <Metrica
        rotulo="Mensajes abiertos"
        valor={numero(datos.mensajes_abiertos)}
        pie="reclamos y avisos sin resolver"
        a={puede('mensajes') ? '/mensajes' : undefined}
      />,
    },
    {
      seccion: 'facturas',
      nodo: <Metrica
        rotulo="Facturas impagas"
        valor={numero(datos.estado_pagos.impaga)}
        pie={`${datos.estado_pagos.parcial} con pago parcial · ${datos.estado_pagos.saldada} saldadas`}
        a={puede('facturas') ? '/facturas' : undefined}
      />,
    },
  ]

  const visibles = tarjetas.filter((tarjeta) => puede(tarjeta.seccion))
  if (!visibles.length) return null

  return (
    <div className="grilla g4">
      {visibles.map((tarjeta, indice) => <div key={indice} style={{ display: 'contents' }}>{tarjeta.nodo}</div>)}
    </div>
  )
}
