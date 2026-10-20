/**
 * Textos da interface. Hoje só pt-BR; o formato (`Messages`) é o contrato que
 * a tradução em inglês vai seguir.
 */
import type { NodeType } from '../api/flowo.gen'

const plural = (count: number, one: string, many: string): string =>
  `${count} ${count === 1 ? one : many}`

export const ptBR = {
  app: {
    name: 'Flowo',
    tagline: 'Automações visuais em uma maquete isométrica',
  },
  health: {
    checking: 'Verificando conexão…',
    connected: 'Conectado ao backend',
    degraded: 'Backend sem banco de dados',
    offline: 'Sem conexão com o backend',
  },
  workflows: {
    title: 'Workflows',
    loading: 'Carregando workflows…',
    loaded: (count: number) => plural(count, 'workflow carregado', 'workflows carregados'),
    empty: 'Nenhum workflow ainda.',
    emptyHint: 'Para criar um exemplo, rode',
    emptyHintCommand: 'make seed',
    error: 'Não foi possível carregar os workflows.',
    retry: 'Tentar novamente',
    nodeCount: (count: number) => plural(count, 'nó', 'nós'),
    edgeCount: (count: number) => plural(count, 'conexão', 'conexões'),
    updatedAt: (date: string) => `Atualizado em ${date}`,
  },
  /** Nome de cada tipo de nó. Um `NodeType` novo sem rótulo quebra a compilação. */
  nodeTypes: {
    manual_trigger: 'Execução manual',
    webhook: 'Webhook',
    schedule: 'Agendamento',
    http_request: 'Requisição HTTP',
    python_script: 'Script Python',
    js_script: 'Script JavaScript',
    email: 'E-mail (Gmail)',
    condition: 'Condição',
    llm: 'LLM',
  } satisfies Record<NodeType, string>,
}

export type Messages = typeof ptBR
