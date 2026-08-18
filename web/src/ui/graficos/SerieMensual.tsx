import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { mesLargo, numero, pesos, pesosCorto } from '../../lib/format'
import { ACENTO, EJE, GRILLA } from './paleta'
import { TooltipCaja } from './TooltipCaja'

export interface PuntoMensual {
  month: string
  revenue_cents: number
  sale_count?: number
  units?: number
}

interface Props {
  datos: PuntoMensual[]
  alto?: number
}

/** Revenue over time. One measure, one axis. */
export function SerieMensual({ datos, alto = 220 }: Props) {
  return (
    <ResponsiveContainer width="100%" height={alto}>
      <AreaChart data={datos} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={GRILLA} vertical={false} />
        <XAxis
          dataKey="month"
          stroke={EJE}
          tickLine={false}
          minTickGap={24}
          tickFormatter={(mes: string) => mes.replace('-', '/').slice(2)}
        />
        <YAxis stroke={EJE} tickLine={false} width={62} tickFormatter={(valor: number) => pesosCorto(valor)} />
        <Tooltip
          cursor={{ stroke: EJE, strokeWidth: 1 }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const punto = payload[0].payload as PuntoMensual
            return (
              <TooltipCaja
                titulo={mesLargo(punto.month)}
                filas={[
                  { texto: 'Facturado', valor: pesos(punto.revenue_cents) },
                  ...(punto.sale_count !== undefined ? [{ texto: 'Ventas', valor: numero(punto.sale_count) }] : []),
                  ...(punto.units !== undefined ? [{ texto: 'Unidades', valor: numero(punto.units) }] : []),
                ]}
              />
            )
          }}
        />
        <Area
          isAnimationActive={false}
          type="monotone"
          dataKey="revenue_cents"
          stroke={ACENTO}
          strokeWidth={2}
          fill={ACENTO}
          fillOpacity={0.1}
          dot={false}
          activeDot={{ r: 4, fill: ACENTO, stroke: '#fff', strokeWidth: 2 }}
          name="Facturado"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
