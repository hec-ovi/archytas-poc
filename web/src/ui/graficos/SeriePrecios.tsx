import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { fecha, numero, pesos, pesosCorto } from '../../lib/format'
import { ACENTO, EJE, GRILLA } from './paleta'
import { TooltipCaja } from './TooltipCaja'
import type { PrecioHistorico } from '../../lib/types'

/** How the price of one article moved. */
export function SeriePrecios({ datos, alto = 200 }: { datos: PrecioHistorico[]; alto?: number }) {
  return (
    <ResponsiveContainer width="100%" height={alto}>
      <LineChart data={datos} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={GRILLA} vertical={false} />
        <XAxis
          dataKey="taken_on"
          stroke={EJE}
          tickLine={false}
          minTickGap={30}
          tickFormatter={(dia: string) => fecha(dia).slice(0, 5)}
        />
        <YAxis stroke={EJE} tickLine={false} width={62} domain={['auto', 'auto']} tickFormatter={(v: number) => pesosCorto(v)} />
        <Tooltip
          cursor={{ stroke: EJE, strokeWidth: 1 }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const punto = payload[0].payload as PrecioHistorico
            return (
              <TooltipCaja
                titulo={fecha(punto.taken_on)}
                filas={[
                  { texto: 'Precio', valor: pesos(punto.price_cents) },
                  { texto: 'Stock', valor: numero(punto.stock) },
                ]}
              />
            )
          }}
        />
        <Line
          type="stepAfter"
          dataKey="price_cents"
          stroke={ACENTO}
          strokeWidth={2}
          dot={{ r: 3, fill: ACENTO, stroke: '#fff', strokeWidth: 1.5 }}
          name="Precio"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
