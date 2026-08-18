/** An error the api answered with, carrying its HTTP status and the Spanish detail. */
export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }

  get sinSesion(): boolean {
    return this.status === 401
  }

  get sinPermiso(): boolean {
    return this.status === 403
  }
}

export function mensajeDeError(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Ocurrio un error inesperado'
}
