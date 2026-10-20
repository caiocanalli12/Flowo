import { useEffect, useId, useRef } from 'react'
import type { WorkflowSummary } from '../../api/flowo.gen'
import { formatDateTime, t } from '../../i18n'
import { useWorkflowListStore, type LoadStatus } from './store'
import styles from './WorkflowList.module.css'

function WorkflowCard({ workflow }: { workflow: WorkflowSummary }) {
  return (
    <li className={styles.card}>
      <h3 className={styles.name}>{workflow.name}</h3>
      <p className={styles.meta}>
        <span>{t.workflows.nodeCount(workflow.node_count)}</span>
        <span aria-hidden="true">·</span>
        <span>{t.workflows.edgeCount(workflow.edge_count)}</span>
      </p>
      <p className={styles.updated}>
        <time dateTime={workflow.updated_at}>
          {t.workflows.updatedAt(formatDateTime(workflow.updated_at))}
        </time>
      </p>
    </li>
  )
}

/** Texto curto para leitores de tela; a região viva fica sempre montada. */
function announcement(status: LoadStatus, count: number): string {
  switch (status) {
    case 'idle':
    case 'loading':
      return t.workflows.loading
    case 'error':
      return t.workflows.error
    case 'ready':
      return count === 0 ? t.workflows.empty : t.workflows.loaded(count)
  }
}

interface WorkflowListBodyProps {
  status: LoadStatus
  items: WorkflowSummary[]
  onRetry: () => void
}

function WorkflowListBody({ status, items, onRetry }: WorkflowListBodyProps) {
  if (status === 'idle' || status === 'loading') {
    return <p className={styles.message}>{t.workflows.loading}</p>
  }

  if (status === 'error') {
    return (
      <div className={styles.message}>
        <p>{t.workflows.error}</p>
        <button type="button" className={styles.button} onClick={onRetry}>
          {t.workflows.retry}
        </button>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className={styles.message}>
        <p>{t.workflows.empty}</p>
        <p className={styles.hint}>
          {t.workflows.emptyHint} <code>{t.workflows.emptyHintCommand}</code>
        </p>
      </div>
    )
  }

  return (
    <ul className={styles.list}>
      {items.map((workflow) => (
        <WorkflowCard key={workflow.id} workflow={workflow} />
      ))}
    </ul>
  )
}

interface WorkflowListProps {
  /** Quando a conexão volta, uma carga que falhou é refeita sozinha. */
  backendConnected: boolean
}

/** Lista de workflows vinda da API. */
export function WorkflowList({ backendConnected }: WorkflowListProps) {
  const headingId = useId()
  const headingRef = useRef<HTMLHeadingElement>(null)
  const status = useWorkflowListStore((state) => state.status)
  const items = useWorkflowListStore((state) => state.items)
  const load = useWorkflowListStore((state) => state.load)
  const retryIfFailed = useWorkflowListStore((state) => state.retryIfFailed)

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (backendConnected) void retryIfFailed()
  }, [backendConnected, retryIfFailed])

  // O botão some durante a nova carga; o foco vai para o título da seção.
  const retry = () => {
    void load().then(() => headingRef.current?.focus())
  }

  return (
    <section className={styles.section} aria-labelledby={headingId}>
      <header className={styles.header}>
        <h2 id={headingId} ref={headingRef} tabIndex={-1} className={styles.title}>
          {t.workflows.title}
        </h2>
        {status === 'ready' && <span className={styles.count}>{items.length}</span>}
      </header>
      <p className={styles.srOnly} role="status">
        {announcement(status, items.length)}
      </p>
      <WorkflowListBody status={status} items={items} onRetry={retry} />
    </section>
  )
}
