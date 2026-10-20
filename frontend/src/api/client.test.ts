import { describe, expect, it } from 'vitest'
import { jsonResponse, mockFetch } from '../test/http'
import { ApiError, apiRequest } from './client'

describe('apiRequest', () => {
  it('devolve o corpo JSON e envia Accept: application/json', async () => {
    const fetchMock = mockFetch(() => Promise.resolve(jsonResponse([{ id: '1' }])))

    await expect(apiRequest('/api/workflows')).resolves.toEqual([{ id: '1' }])

    const init = fetchMock.mock.calls[0]?.[1]
    expect(new Headers(init?.headers).get('Accept')).toBe('application/json')
  })

  it('marca o corpo como JSON quando envia dados', async () => {
    const fetchMock = mockFetch(() => Promise.resolve(jsonResponse({}, 201)))

    await apiRequest('/api/workflows', { method: 'POST', body: JSON.stringify({ name: 'x' }) })

    const init = fetchMock.mock.calls[0]?.[1]
    expect(new Headers(init?.headers).get('Content-Type')).toBe('application/json')
  })

  it('lança ApiError com status e corpo JSON em respostas de erro', async () => {
    mockFetch(() => Promise.resolve(jsonResponse({ detail: 'Workflow not found' }, 404)))

    const error = await apiRequest('/api/workflows/x').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 404, body: { detail: 'Workflow not found' } })
  })

  it('guarda o texto bruto quando o erro não é JSON', async () => {
    mockFetch(() => Promise.resolve(new Response('Bad Gateway', { status: 502 })))

    await expect(apiRequest('/api/health')).rejects.toMatchObject({
      status: 502,
      body: 'Bad Gateway',
    })
  })

  it('devolve undefined para respostas sem corpo', async () => {
    mockFetch(() => Promise.resolve(new Response(null, { status: 204 })))

    await expect(apiRequest('/api/workflows/x', { method: 'DELETE' })).resolves.toBeUndefined()
  })
})
