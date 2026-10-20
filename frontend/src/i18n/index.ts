import { ptBR, type Messages } from './messages'

export const locale = 'pt-BR'

/** Textos da interface no idioma ativo. Componentes nunca escrevem textos soltos. */
export const t: Messages = ptBR

const dateTimeFormat = new Intl.DateTimeFormat(locale, { dateStyle: 'short', timeStyle: 'short' })

/** Data e hora curtas no idioma ativo, a partir de um ISO 8601 vindo da API. */
export function formatDateTime(iso: string): string {
  return dateTimeFormat.format(new Date(iso))
}
