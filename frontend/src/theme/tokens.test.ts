// @vitest-environment node
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import schema from '../../../shared/schema/flowo.schema.json'
import { cssVar, cssVariables, nodeLight, nodeLightVar } from './tokens'

// Lido do disco: no Vitest o CSS não é processado (um import `?raw` chega vazio).
const tokensCss = readFileSync(join(dirname(fileURLToPath(import.meta.url)), 'tokens.css'), 'utf8')

const normalize = (value: string) => value.replace(/\s+/g, ' ').trim().toLowerCase()

function declaredVariables(css: string): Record<string, string> {
  const declared: Record<string, string> = {}
  for (const match of css.matchAll(/(--flowo-[\w-]+)\s*:\s*([^;]+);/g)) {
    const [, name, value] = match
    if (name !== undefined && value !== undefined) declared[name] = normalize(value)
  }
  return declared
}

describe('design tokens', () => {
  it('tokens.css declara exatamente as variáveis de tokens.ts', () => {
    const expected = Object.fromEntries(
      Object.entries(cssVariables()).map(([name, value]) => [name, normalize(value)]),
    )

    expect(declaredVariables(tokensCss)).toEqual(expected)
  })

  it('toda NodeType do contrato tem uma luz', () => {
    const nodeTypes = schema.$defs.NodeType.enum

    expect(Object.keys(nodeLight).sort()).toEqual([...nodeTypes].sort())
  })

  it('gera referências var(...) com nomes em kebab-case', () => {
    expect(cssVar('gray', 'textMuted')).toBe('var(--flowo-gray-text-muted)')
    expect(nodeLightVar('condition')).toBe('var(--flowo-light-condition)')
    expect(nodeLightVar('webhook')).toBe('var(--flowo-light-trigger)')
  })
})
