import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { pesos, pesosCorto } from '../../lib/format'
import { ACENTO, EJE, GRILLA } from './paleta'
import { TooltipCaja } from './TooltipCaja'

export interface BarraCategoria {
  etiqueta: string
  valor: number
  nota?: string
}

interface Props {
  datos: BarraCategoria[]
  alto?: number
  tituloValor?: string
}

/** Magnitude across a handful of named things, laid out horizontally so the names fit. */
export function BarrasCategoria({ datos, alto, tituloValor = 'Total' }: Props) {
  const altura = alto ?? Math.max(140, datos.length * 30 + 24)
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <BarChart data={datos} layout="vertical" margin={{ top: 4, right: 16, left: 0, bottom: 4 }} barCategoryGap={6}>
        <CartesianGrid stroke={GRILLA} horizontal={false} />
        <XAxis type="number" stroke={EJE} tickLine={false} tickFormatter={(valor: number) => pesosCorto(valor)} />
        <YAxis type="category" dataKey="etiqueta" stroke={EJE} tickLine={false} width={150} interval={0} />
        <Tooltip
          cursor={{ fill: 'rgba(10, 92, 102, 0.06)' }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const punto = payload[0].payload as BarraCategoria
            return (
              <TooltipCaja
                titulo={punto.etiqueta}
                filas={[
                  { texto: tituloValor, valor: pesos(punto.valor) },
                  ...(punto.nota ? [{ texto: 'Detalle', valor: punto.nota }] : []),
                ]}
              />
            )
          }}
        />
        <Bar dataKey="valor" fill={ACENTO} maxBarSize={16} name={tituloValor} />
      </BarChart>
    </ResponsiveContainer>
  )
}
