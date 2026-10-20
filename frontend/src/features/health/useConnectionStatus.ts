import { useEffect, useState } from 'react'
import { fetchConnectionStatus, type ConnectionStatus } from './api'

export const HEALTH_POLL_INTERVAL_MS = 10_000
export const HEALTH_REQUEST_TIMEOUT_MS = 5_000

export type ConnectionState = ConnectionStatus | 'checking'

/**
 * Consulta a saúde do backend ao montar e depois a cada `intervalMs`.
 * Uma consulta só começa quando a anterior termina, e cada uma tem timeout.
 */
export function useConnectionStatus(
  intervalMs = HEALTH_POLL_INTERVAL_MS,
  timeoutMs = HEALTH_REQUEST_TIMEOUT_MS,
): ConnectionState {
  const [state, setState] = useState<ConnectionState>('checking')

  useEffect(() => {
    let active = true
    let controller: AbortController | undefined
    let pollTimer: ReturnType<typeof setTimeout> | undefined

    const check = async (): Promise<void> => {
      const request = new AbortController()
      controller = request
      const timeout = setTimeout(() => {
        request.abort()
      }, timeoutMs)
      const next = await fetchConnectionStatus(request.signal)
      clearTimeout(timeout)
      if (!active) return
      setState(next)
      pollTimer = setTimeout(() => void check(), intervalMs)
    }

    void check()
    return () => {
      active = false
      controller?.abort()
      clearTimeout(pollTimer)
    }
  }, [intervalMs, timeoutMs])

  return state
}
