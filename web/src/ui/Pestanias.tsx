export interface Pestania<T extends string> {
  clave: T
  texto: string
  cuenta?: number
}

interface Props<T extends string> {
  opciones: Pestania<T>[]
  activa: T
  onCambiar: (clave: T) => void
}

export function Pestanias<T extends string>({ opciones, activa, onCambiar }: Props<T>) {
  return (
    <div className="pestanias" role="tablist">
      {opciones.map((opcion) => (
        <button
          key={opcion.clave}
          role="tab"
          aria-selected={opcion.clave === activa}
          className={opcion.clave === activa ? 'pestania activa' : 'pestania'}
          onClick={() => onCambiar(opcion.clave)}
        >
          {opcion.texto}
          {opcion.cuenta === undefined ? null : <span className="tenue"> ({opcion.cuenta})</span>}
        </button>
      ))}
    </div>
  )
}
