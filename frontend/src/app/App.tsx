import { ConnectionIndicator } from '../features/health/ConnectionIndicator'
import { useConnectionStatus } from '../features/health/useConnectionStatus'
import { WorkflowList } from '../features/workflows/WorkflowList'
import { t } from '../i18n'
import styles from './App.module.css'

/** Marca do Flowo: um bloco isométrico em cinzas, como as construções da maquete. */
function Logo() {
  return (
    <svg className={styles.logo} viewBox="0 0 32 32" aria-hidden="true">
      <path className={styles.logoTop} d="M16 3 28 10 16 17 4 10Z" />
      <path className={styles.logoLeft} d="M4 10 16 17V30L4 23Z" />
      <path className={styles.logoRight} d="M28 10 16 17V30L28 23Z" />
    </svg>
  )
}

export function App() {
  const connection = useConnectionStatus()

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <div className={styles.brand}>
          <Logo />
          <h1 className={styles.wordmark}>{t.app.name}</h1>
          <span className={styles.tagline}>{t.app.tagline}</span>
        </div>
        <ConnectionIndicator state={connection} />
      </header>
      <main className={styles.main}>
        <WorkflowList backendConnected={connection === 'connected'} />
      </main>
    </div>
  )
}
