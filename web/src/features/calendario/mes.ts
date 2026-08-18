// Month arithmetic on plain ISO strings, so no timezone ever shifts a due date.

export interface Mes {
  anio: number
  mes: number // 1-12
}

export const DIAS_SEMANA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

export function mesDeHoy(): Mes {
  const hoy = new Date()
  return { anio: hoy.getFullYear(), mes: hoy.getMonth() + 1 }
}

export function hoyISO(): string {
  const hoy = new Date()
  return iso(hoy.getFullYear(), hoy.getMonth() + 1, hoy.getDate())
}

export function iso(anio: number, mes: number, dia: number): string {
  return `${anio}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`
}

export function correrMes({ anio, mes }: Mes, pasos: number): Mes {
  const total = anio * 12 + (mes - 1) + pasos
  return { anio: Math.floor(total / 12), mes: (total % 12) + 1 }
}

export function primerDia({ anio, mes }: Mes): string {
  return iso(anio, mes, 1)
}

export interface Casilla {
  fecha: string
  dia: number
  delMes: boolean
  esHoy: boolean
  finDeSemana: boolean
}

/** Six weeks starting on the Monday on or before the first, so the grid never jumps. */
export function armarGrilla({ anio, mes }: Mes): Casilla[] {
  const primero = new Date(Date.UTC(anio, mes - 1, 1))
  const corrimiento = (primero.getUTCDay() + 6) % 7
  const arranque = new Date(Date.UTC(anio, mes - 1, 1 - corrimiento))
  const hoy = hoyISO()

  return Array.from({ length: 42 }, (_, indice) => {
    const dia = new Date(arranque.getTime() + indice * 86400000)
    const fecha = iso(dia.getUTCFullYear(), dia.getUTCMonth() + 1, dia.getUTCDate())
    const diaSemana = (dia.getUTCDay() + 6) % 7
    return {
      fecha,
      dia: dia.getUTCDate(),
      delMes: dia.getUTCMonth() + 1 === mes && dia.getUTCFullYear() === anio,
      esHoy: fecha === hoy,
      finDeSemana: diaSemana >= 5,
    }
  })
}
