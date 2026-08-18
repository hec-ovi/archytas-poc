import { api } from '../../lib/api'
import { useRecurso } from '../../lib/useRecurso'
import { fecha, numero, pesos } from '../../lib/format'
import { Bloque } from '../../ui/Estado'
import { Modal } from '../../ui/Modal'
import { TablaCaja } from '../../ui/Tabla'
import { SeriePrecios } from '../../ui/graficos/SeriePrecios'

/** How the price of one article moved, with the readings behind the line. */
export function ModalPrecios({ id, onCerrar }: { id: number; onCerrar: () => void }) {
  const recurso = useRecurso(() => api.productos.precios(id), [id])

  return (
    <Modal
      titulo={
        <>
          <strong>{recurso.datos?.producto.code ?? 'Artículo'}</strong>
          <span className="tenue">{recurso.datos?.producto.description ?? ''}</span>
        </>
      }
      onCerrar={onCerrar}
    >
      <Bloque recurso={recurso} que="Cargando la historia de precios">
        {(datos) => (
          <div className="pila">
            <dl className="definiciones">
              <dt>Rubro</dt><dd>{datos.producto.subcategory ?? '-'}</dd>
              <dt>Precio actual</dt><dd className="num fuerte">{pesos(datos.producto.price_cents)}</dd>
              <dt>Stock</dt><dd className="num">{numero(datos.producto.stock)}</dd>
              <dt>Visto por primera vez</dt><dd>{fecha(datos.producto.first_seen)}</dd>
            </dl>

            {datos.historial.length > 1 ? (
              <SeriePrecios datos={datos.historial} alto={220} />
            ) : (
              <div className="aviso">
                Todavía hay una sola lectura de precio de este artículo. La historia se arma con cada
                actualización desde el portal.
              </div>
            )}

            <TablaCaja alto={240}>
              <table className="tabla">
                <thead>
                  <tr><th>Fecha</th><th className="num">Precio</th><th className="num">Stock</th><th>Origen</th></tr>
                </thead>
                <tbody>
                  {datos.historial.map((lectura) => (
                    <tr key={`${lectura.taken_on}-${lectura.price_cents}`}>
                      <td className="num">{fecha(lectura.taken_on)}</td>
                      <td className="num fuerte">{pesos(lectura.price_cents)}</td>
                      <td className="num">{numero(lectura.stock)}</td>
                      <td className="tenue">{lectura.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TablaCaja>
          </div>
        )}
      </Bloque>
    </Modal>
  )
}
