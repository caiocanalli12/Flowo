import { render, screen, within } from '@testing-library/react'
import { beforeEach, expect, it } from 'vitest'
import { useWorkflowListStore } from '../features/workflows/store'
import { jsonResponse, mockFetch } from '../test/http'
import { App } from './App'

beforeEach(() => {
  useWorkflowListStore.setState(useWorkflowListStore.getInitialState(), true)
})

it('mostra a conexão com o backend e a lista de workflows', async () => {
  mockFetch((input) => {
    const url = input instanceof Request ? input.url : String(input)
    if (url.endsWith('/api/health')) {
      return Promise.resolve(jsonResponse({ status: 'ok', database: 'ok', version: '0.1.0' }))
    }
    return Promise.resolve(
      jsonResponse([
        {
          id: '6f1c2a8e-0000-4000-8000-000000000001',
          name: 'Exemplo',
          node_count: 2,
          edge_count: 1,
          created_at: '2026-10-19T12:00:00Z',
          updated_at: '2026-10-20T09:30:00Z',
        },
      ]),
    )
  })

  render(<App />)

  expect(screen.getByRole('heading', { level: 1, name: 'Flowo' })).toBeInTheDocument()
  expect(await screen.findByText('Conectado ao backend')).toBeInTheDocument()
  const list = await screen.findByRole('list')
  expect(within(list).getByRole('heading', { name: 'Exemplo' })).toBeInTheDocument()
})
