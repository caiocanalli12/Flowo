/**
 * Gera `src/api/flowo.gen.ts` a partir de `shared/schema/flowo.schema.json`.
 *
 * O schema vem dos modelos Pydantic do backend: o frontend nunca define os
 * tipos do contrato à mão. Uso: `npm run gen:types` (ou `make types` na raiz).
 */
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { compile, type Options } from 'json-schema-to-typescript'

const here = dirname(fileURLToPath(import.meta.url))

// No container o frontend fica em /app e o shared em /shared: mesmo layout relativo.
export const SCHEMA_PATH = resolve(here, '../../shared/schema/flowo.schema.json')
export const OUTPUT_PATH = resolve(here, '../src/api/flowo.gen.ts')

const BANNER = `/* eslint-disable */
/**
 * ARQUIVO GERADO - não edite à mão.
 * Fonte: modelos Pydantic do backend -> shared/schema/flowo.schema.json.
 * Para regenerar: \`make types\` (na raiz) ou \`npm run gen:types\`.
 */`

const OPTIONS: Partial<Options> = {
  bannerComment: BANNER,
  additionalProperties: false,
  style: { semi: false, singleQuote: true, trailingComma: 'all', printWidth: 100 },
}

export async function generateTypes(): Promise<string> {
  const schema: unknown = JSON.parse(await readFile(SCHEMA_PATH, 'utf8'))
  // Cast: o arquivo é gerado pelo Pydantic e sempre é um JSON Schema válido;
  // validá-lo de novo aqui não acrescentaria nada.
  return compile(schema as Parameters<typeof compile>[0], 'FlowoContract', {
    ...OPTIONS,
    cwd: dirname(SCHEMA_PATH),
  })
}

async function main(): Promise<void> {
  await mkdir(dirname(OUTPUT_PATH), { recursive: true })
  await writeFile(OUTPUT_PATH, await generateTypes(), 'utf8')
  console.log(`Tipos TypeScript escritos em ${OUTPUT_PATH}`)
}

const invokedDirectly =
  process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url)

if (invokedDirectly) {
  await main()
}
