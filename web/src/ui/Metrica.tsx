import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

export type TonoMetrica = 'urgente' | 'aviso' | 'calma' | 'neutro'

interface Props {
  rotulo: string
  valor: ReactNode
  pie?: ReactNode
  tono?: TonoMetrica
  a?: string
}

export function Metrica({ rotulo, valor, pie, tono = 'neutro', a }: Props) {
  const clases = ['metrica', tono === 'neutro' ? '' : tono].filter(Boolean).join(' ')
  const cuerpo = (
    <>
      <span className="rotulo">{rotulo}</span>
      <span className="valor">{valor}</span>
      {pie ? <span className="pie">{pie}</span> : null}
    </>
  )
  if (a) return <Link className={clases} to={a}>{cuerpo}</Link>
  return <div className={clases}>{cuerpo}</div>
}
