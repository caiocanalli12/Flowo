import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import type { WorkflowSummary } from '../../api/flowo.gen'
import { formatDateTime } from '../../i18n'
import { jsonResponse, mockFetch } from '../../test/http'
import { useWorkflowListStore } from './store'
import { WorkflowList } from './WorkflowList'

const EXAMPLE: WorkflowSummary = {
  id: '6f1c2a8e-0000-4000-8000-000000000001',
  name: 'Exemplo: Webhook → HTTP → Condição',
  node_count: 5,
  edge_count: 4,
  created_at: '2026-10-19T12:00:00Z',
  updated_at: '2026-10-20T09:30:00Z',
}

const SINGLE: WorkflowSummary = {
  ...EXAMPLE,
  id: '6f1c2a8e-0000-4000-8000-000000000002',
  name: 'Só um nó',
  node_count: 1,
  edge_count: 1,
}

/** Primeira chamada falha (500), as seguintes devolvem `items`. */
function failOnceThen(items: WorkflowSummary[]) {
  let calls = 0
  return mockFetch(() => {
    calls += 1
    return Promise.resolve(
      calls === 1 ? jsonResponse({ detail: 'boom' }, 500) : jsonResponse(items),
    )
  })
}

beforeEach(() => {
  useWorkflowListStore.setState(useWorkflowListStore.getInitialState(), true)
})

describe('WorkflowList', () => {
  it('lista os workflows com contagens e data de atualização', async () => {
    const fetchMock = mockFetch(() => Promise.resolve(jsonResponse([EXAMPLE, SINGLE])))

    render(<WorkflowList backendConnected />)

    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(2)
    const [first, second] = items as [HTMLElement, HTMLElement]
    expect(within(first).getByRole('heading', { name: EXAMPLE.name })).toBeInTheDocument()
    expect(first).toHaveTextContent('5 nós')
    expect(first).toHaveTextContent('4 conexões')
    expect(first).toHaveTextContent(`Atualizado em ${formatDateTime(EXAMPLE.updated_at)}`)
    expect(second).toHaveTextContent('1 nó')
    expect(second).toHaveTextContent('1 conexão')
    expect(screen.getByRole('heading', { name: 'Workflows' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('2 workflows carregados')
    expect(fetchMock).toHaveBeenCalledWith('/api/workflows', expect.anything())
  })

  it('anuncia o carregamento enquanto a API não responde', () => {
    mockFetch(() => new Promise<Response>(() => undefined))

    render(<WorkflowList backendConnected />)

    expect(screen.getByRole('status')).toHaveTextContent('Carregando workflows…')
  })

  it('mostra o estado vazio com a dica do seed', async () => {
    mockFetch(() => Promise.resolve(jsonResponse([])))

    render(<WorkflowList backendConnected />)

    expect(await screen.findByText('make seed')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Nenhum workflow ainda.')
  })

  it('mostra o erro, tenta de novo ao clicar e devolve o foco ao título', async () => {
    failOnceThen([EXAMPLE])
    const user = userEvent.setup()

    render(<WorkflowList backendConnected={false} />)

    const retry = await screen.findByRole('button', { name: 'Tentar novamente' })
    expect(screen.getByRole('status')).toHaveTextContent('Não foi possível carregar os workflows.')

    await user.click(retry)

    expect(await screen.findByRole('heading', { name: EXAMPLE.name })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Tentar novamente' })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Workflows' })).toHaveFocus()
  })

  it('recarrega sozinha quando a conexão com o backend volta', async () => {
    const fetchMock = failOnceThen([EXAMPLE])

    const { rerender } = render(<WorkflowList backendConnected={false} />)
    await screen.findByRole('button', { name: 'Tentar novamente' })

    rerender(<WorkflowList backendConnected />)

    expect(await screen.findByRole('heading', { name: EXAMPLE.name })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})

describe('useWorkflowListStore', () => {
  it('não dispara uma segunda requisição enquanto a primeira está em andamento', async () => {
    let resolve: (response: Response) => void = () => undefined
    const fetchMock = mockFetch(
      () =>
        new Promise<Response>((r) => {
          resolve = r
        }),
    )

    const { load } = useWorkflowListStore.getState()
    const first = load()
    const second = load()
    resolve(jsonResponse([EXAMPLE]))
    await Promise.all([first, second])

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(useWorkflowListStore.getState()).toMatchObject({ status: 'ready', items: [EXAMPLE] })
  })

  it('retryIfFailed só recarrega depois de uma falha', async () => {
    const fetchMock = failOnceThen([EXAMPLE])
    const store = useWorkflowListStore.getState()

    await store.retryIfFailed()
    expect(fetchMock).not.toHaveBeenCalled()

    await store.load()
    expect(useWorkflowListStore.getState().status).toBe('error')

    await store.retryIfFailed()
    expect(useWorkflowListStore.getState()).toMatchObject({ status: 'ready', items: [EXAMPLE] })
  })
})
