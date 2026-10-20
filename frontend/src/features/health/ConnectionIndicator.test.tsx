import { render, renderHook, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { jsonResponse, mockFetch } from '../../test/http'
import { ConnectionIndicator } from './ConnectionIndicator'
import { useConnectionStatus, type ConnectionState } from './useConnectionStatus'

const HEALTHY = { status: 'ok', database: 'ok', version: '0.1.0' }
const DEGRADED = { status: 'degraded', database: 'unavailable', version: '0.1.0' }

describe('ConnectionIndicator', () => {
  it.each<[ConnectionState, string]>([
    ['checking', 'Verificando conexão…'],
    ['connected', 'Conectado ao backend'],
    ['degraded', 'Backend sem banco de dados'],
    ['offline', 'Sem conexão com o backend'],
  ])('mostra o estado %s', (state, label) => {
    render(<ConnectionIndicator state={state} />)

    const indicator = screen.getByRole('status')
    expect(indicator).toHaveTextContent(label)
    expect(indicator).toHaveAttribute('data-state', state)
  })
})

describe('useConnectionStatus', () => {
  it('começa em "checking" antes da primeira resposta', () => {
    mockFetch(() => new Promise<Response>(() => undefined))

    const { result } = renderHook(() => useConnectionStatus())

    expect(result.current).toBe('checking')
  })

  it.each<[string, () => Promise<Response>, ConnectionState]>([
    ['health ok', () => Promise.resolve(jsonResponse(HEALTHY)), 'connected'],
    ['503 com corpo de health', () => Promise.resolve(jsonResponse(DEGRADED, 503)), 'degraded'],
    ['falha de rede', () => Promise.reject(new TypeError('Failed to fetch')), 'offline'],
    [
      'proxy sem backend (502)',
      () => Promise.resolve(new Response('', { status: 502 })),
      'offline',
    ],
  ])('traduz %s', async (_case, respond, expected) => {
    mockFetch(respond)

    const { result } = renderHook(() => useConnectionStatus())

    await waitFor(() => {
      expect(result.current).toBe(expected)
    })
  })

  it('volta a consultar no intervalo e reflete a recuperação do backend', async () => {
    let calls = 0
    mockFetch(() => {
      calls += 1
      return calls === 1
        ? Promise.reject(new TypeError('Failed to fetch'))
        : Promise.resolve(jsonResponse(HEALTHY))
    })

    const { result } = renderHook(() => useConnectionStatus(300))

    await waitFor(() => {
      expect(result.current).toBe('offline')
    })
    await waitFor(() => {
      expect(result.current).toBe('connected')
    })
    expect(calls).toBe(2)
  })

  it('dá timeout em requisições que não respondem', async () => {
    mockFetch(
      (_input, init) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () => {
            reject(new DOMException('Aborted', 'AbortError'))
          })
        }),
    )

    const { result } = renderHook(() => useConnectionStatus(10_000, 20))

    await waitFor(() => {
      expect(result.current).toBe('offline')
    })
  })

  it('cancela a requisição em andamento ao desmontar', () => {
    let signal: AbortSignal | undefined
    mockFetch((_input, init) => {
      signal = init?.signal ?? undefined
      return new Promise<Response>(() => undefined)
    })

    const { unmount } = renderHook(() => useConnectionStatus())
    unmount()

    expect(signal?.aborted).toBe(true)
  })
})
