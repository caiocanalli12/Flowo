import { ApiError, apiRequest } from '../../api/client'
import type { HealthStatus } from '../../api/flowo.gen'

export type ConnectionStatus = 'connected' | 'degraded' | 'offline'

function isHealthStatus(value: unknown): value is HealthStatus {
  return (
    typeof value === 'object' &&
    value !== null &&
    'status' in value &&
    (value.status === 'ok' || value.status === 'degraded')
  )
}

/**
 * Consulta `/api/health` e traduz para o estado da conexão. Nunca lança:
 * qualquer falha (rede, timeout, abort, proxy sem backend) vira `offline`.
 */
export async function fetchConnectionStatus(signal?: AbortSignal): Promise<ConnectionStatus> {
  try {
    const body = await apiRequest('/api/health', { signal })
    if (isHealthStatus(body)) return body.status === 'ok' ? 'connected' : 'degraded'
    return 'offline'
  } catch (error) {
    // 503 com corpo de health: a API respondeu, mas o banco não.
    if (error instanceof ApiError && error.status === 503 && isHealthStatus(error.body)) {
      return 'degraded'
    }
    return 'offline'
  }
}
