// @vitest-environment node
import { readFile } from 'node:fs/promises'
import { expect, it } from 'vitest'
import { generateTypes, OUTPUT_PATH } from '../../scripts/gen-types'

it('flowo.gen.ts está em dia com o JSON Schema do contrato', async () => {
  const committed = (await readFile(OUTPUT_PATH, 'utf8')).replace(/\r\n/g, '\n')
  const expected = await generateTypes()

  expect(committed, 'Tipos desatualizados: rode `make types` (ou `npm run gen:types`).').toBe(
    expected,
  )
})
