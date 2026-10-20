import { create } from 'zustand'
import type { WorkflowSummary } from '../../api/flowo.gen'
import { fetchWorkflowSummaries } from './api'

export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error'

interface WorkflowListState {
  status: LoadStatus
  items: WorkflowSummary[]
  load: () => Promise<void>
  /** Recarrega só se a última tentativa falhou (ex.: o backend acabou de voltar). */
  retryIfFailed: () => Promise<void>
}

export const useWorkflowListStore = create<WorkflowListState>()((set, get) => ({
  status: 'idle',
  items: [],
  load: async () => {
    // Evita requisições duplicadas (ex.: efeitos rodando duas vezes no StrictMode).
    if (get().status === 'loading') return
    set({ status: 'loading' })
    try {
      set({ status: 'ready', items: await fetchWorkflowSummaries() })
    } catch {
      set({ status: 'error' })
    }
  },
  retryIfFailed: async () => {
    if (get().status === 'error') await get().load()
  },
}))
