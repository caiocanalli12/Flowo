/**
 * Cliente HTTP mínimo da API. Usa caminhos relativos (`/api/...`): em
 * desenvolvimento o Vite faz o proxy para o backend.
 */

export class ApiError extends Error {
  readonly status: number
  /** Corpo da resposta: JSON quando possível, senão o texto bruto. */
  readonly body: unknown

  constructor(status: number, body: unknown) {
    super(`API request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

async function readBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (text === '') return undefined
  try {
    return JSON.parse(text) as unknown
  } catch {
    return text
  }
}

/**
 * Faz a requisição e devolve o corpo já lido. Lança `ApiError` para status
 * fora de 2xx (com o corpo disponível em `error.body`).
 */
export async function apiRequest(path: string, init: RequestInit = {}): Promise<unknown> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(path, { ...init, headers })
  const body = await readBody(response)
  if (!response.ok) throw new ApiError(response.status, body)
  return body
}
