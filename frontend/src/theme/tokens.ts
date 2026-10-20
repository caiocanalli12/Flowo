/**
 * Design tokens do Flowo. Espelhados como CSS variables em `tokens.css`
 * (um teste garante que os dois não divergem).
 *
 * Regra visual: a cena é toda em cinzas; só as luzes têm cor (uma por tipo
 * de nó), e os estados usam verde (sucesso) e vermelho (falha).
 * Componentes nunca usam hex direto: usam `cssVar(...)` ou as variáveis CSS.
 */
import type { NodeType } from '../api/flowo.gen'

export const colors = {
  gray: {
    background: '#1C1D21',
    surface: '#26282D',
    grid: '#34363C',
    border: '#44474F',
    text: '#E6E7EA',
    textMuted: '#9A9DA6',
  },
  light: {
    trigger: '#FB923C',
    http: '#6366F1',
    python: '#38BDF8',
    javascript: '#FACC15',
    email: '#F472B6',
    condition: '#E5E7EB',
    llm: '#A855F7',
  },
  status: {
    success: '#22C55E',
    failure: '#EF4444',
  },
} as const

export type ColorGroup = keyof typeof colors
export type ColorToken<G extends ColorGroup> = keyof (typeof colors)[G] & string
export type LightColor = ColorToken<'light'>

/** Cor da luz de cada tipo de nó. Um `NodeType` novo sem cor quebra a compilação. */
export const nodeLight = {
  manual_trigger: 'trigger',
  webhook: 'trigger',
  schedule: 'trigger',
  http_request: 'http',
  python_script: 'python',
  js_script: 'javascript',
  email: 'email',
  condition: 'condition',
  llm: 'llm',
} as const satisfies Record<NodeType, LightColor>

export const typography = {
  fontSans:
    "Inter, 'Segoe UI', system-ui, -apple-system, Roboto, 'Helvetica Neue', Arial, sans-serif",
  fontMono: "'JetBrains Mono', 'Cascadia Code', Consolas, 'SFMono-Regular', monospace",
} as const

export const radius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
} as const

export const space = {
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  6: '24px',
  8: '32px',
} as const

const kebab = (value: string): string => value.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`)

/** Nome da variável CSS de uma cor, ex.: `--flowo-gray-text-muted`. */
export function cssVarName<G extends ColorGroup>(group: G, token: ColorToken<G>): string {
  return `--flowo-${group}-${kebab(token)}`
}

/** Referência `var(...)` para usar em estilos inline. */
export function cssVar<G extends ColorGroup>(group: G, token: ColorToken<G>): string {
  return `var(${cssVarName(group, token)})`
}

/** Cor da luz de um tipo de nó como `var(...)`. */
export function nodeLightVar(type: NodeType): string {
  return cssVar('light', nodeLight[type])
}

/** Todas as variáveis CSS que `tokens.css` precisa declarar, com seus valores. */
export function cssVariables(): Record<string, string> {
  const vars: Record<string, string> = {}
  for (const [group, tokens] of Object.entries(colors)) {
    for (const [token, value] of Object.entries(tokens)) {
      vars[`--flowo-${group}-${kebab(token)}`] = value
    }
  }
  vars['--flowo-font-sans'] = typography.fontSans
  vars['--flowo-font-mono'] = typography.fontMono
  for (const [key, value] of Object.entries(radius)) vars[`--flowo-radius-${key}`] = value
  for (const [key, value] of Object.entries(space)) vars[`--flowo-space-${key}`] = value
  return vars
}
