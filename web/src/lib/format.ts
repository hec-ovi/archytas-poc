// The only place amounts, dates and numbers get turned into text.

const money = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 0 })
const decimal = new Intl.NumberFormat('es-AR')
const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

/** Integer cents to `$1.399.069`. */
export function pesos(centavos: number | null | undefined): string {
  if (centavos === null || centavos === undefined) return '-'
  return `$${money.format(Math.round(centavos / 100))}`
}

/** Short form for chart axes: `$1,4 M`, `$820 k`. */
export function pesosCorto(centavos: number | null | undefined): string {
  if (centavos === null || centavos === undefined) return '-'
  const value = Math.round(centavos / 100)
  if (Math.abs(value) >= 1_000_000) return `$${decimal.format(Number((value / 1_000_000).toFixed(1)))} M`
  if (Math.abs(value) >= 1_000) return `$${Math.round(value / 1_000)} k`
  return `$${money.format(value)}`
}

export function numero(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-'
  return decimal.format(value)
}

/** ISO `2026-08-21` to `21/08/2026`. Tolerates a full timestamp. */
export function fecha(iso: string | null | undefined): string {
  if (!iso) return '-'
  const [dia] = iso.split(/[T ]/)
  const partes = dia.split('-')
  if (partes.length !== 3) return iso
  return `${partes[2]}/${partes[1]}/${partes[0]}`
}

/** ISO timestamp to `21/08/2026 14:03`. */
export function fechaHora(iso: string | null | undefined): string {
  if (!iso) return '-'
  const parsed = new Date(iso.includes('T') ? iso : iso.replace(' ', 'T') + 'Z')
  if (Number.isNaN(parsed.getTime())) return fecha(iso)
  return `${fecha(iso)} ${String(parsed.getHours()).padStart(2, '0')}:${String(parsed.getMinutes()).padStart(2, '0')}`
}

/** `2026-08` to `ago 2026`. */
export function mesCorto(month: string): string {
  const [anio, mes] = month.split('-')
  const nombre = MESES[Number(mes) - 1]
  return nombre ? `${nombre.slice(0, 3)} ${anio}` : month
}

/** `2026-08` to `agosto 2026`. */
export function mesLargo(month: string): string {
  const [anio, mes] = month.split('-')
  const nombre = MESES[Number(mes) - 1]
  return nombre ? `${nombre} ${anio}` : month
}

export function nombreMes(indice: number): string {
  return MESES[indice] ?? ''
}

/** Days overdue as plain words: positive means already late. */
export function atraso(dias: number | null | undefined): string {
  if (dias === null || dias === undefined) return '-'
  if (dias > 0) return `${numero(dias)} d vencida`
  if (dias === 0) return 'vence hoy'
  return `en ${numero(-dias)} d`
}

export function diasTexto(dias: number | null | undefined): string {
  if (dias === null || dias === undefined) return '-'
  return `${numero(dias)} d`
}
