import { t } from '../../i18n'
import styles from './ConnectionIndicator.module.css'
import type { ConnectionState } from './useConnectionStatus'

const LABELS: Record<ConnectionState, string> = {
  checking: t.health.checking,
  connected: t.health.connected,
  degraded: t.health.degraded,
  offline: t.health.offline,
}

/** Selo com a luz de status da conexão com o backend. */
export function ConnectionIndicator({ state }: { state: ConnectionState }) {
  return (
    <div className={styles.indicator} data-state={state} role="status" aria-live="polite">
      <span className={styles.light} aria-hidden="true" />
      <span>{LABELS[state]}</span>
    </div>
  )
}
