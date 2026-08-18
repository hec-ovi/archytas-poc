import type { ButtonHTMLAttributes } from 'react'

type Variante = 'normal' | 'principal' | 'peligro' | 'plano'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variante
  chico?: boolean
}

export function Boton({ variante = 'normal', chico, className, type = 'button', ...resto }: Props) {
  const clases = [
    'boton',
    variante === 'normal' ? '' : variante,
    chico ? 'chico' : '',
    className ?? '',
  ].filter(Boolean).join(' ')
  return <button type={type} className={clases} {...resto} />
}
