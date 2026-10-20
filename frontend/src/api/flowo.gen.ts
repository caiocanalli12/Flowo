/* eslint-disable */
/**
 * ARQUIVO GERADO - não edite à mão.
 * Fonte: modelos Pydantic do backend -> shared/schema/flowo.schema.json.
 * Para regenerar: `make types` (na raiz) ou `npm run gen:types`.
 */

/**
 * Tipos de nó suportados por um workflow.
 */
export type NodeType =
  | 'manual_trigger'
  | 'webhook'
  | 'schedule'
  | 'http_request'
  | 'python_script'
  | 'js_script'
  | 'email'
  | 'condition'
  | 'llm'

/**
 * Contrato da API do Flowo. GERADO a partir dos modelos Pydantic do backend; não edite à mão (rode `make types`).
 */
export interface FlowoContract {
  Workflow?: Workflow
  WorkflowSummary?: WorkflowSummary
  WorkflowCreate?: WorkflowCreate
  WorkflowUpdate?: WorkflowUpdate
  Node?: Node
  Edge?: Edge
  EdgeEndpoint?: EdgeEndpoint
  Position?: Position
  HealthStatus?: HealthStatus
}
/**
 * Workflow persistido, como a API o devolve.
 */
export interface Workflow {
  id: string
  name: string
  nodes: Node[]
  edges: Edge[]
  created_at: string
  updated_at: string
}
/**
 * Um passo do fluxo.
 *
 * Todos os campos são obrigatórios (`label` pode ser vazio, `config` pode ser `{}`):
 * assim o mesmo tipo serve para entrada e resposta, sem campos opcionais no TS.
 */
export interface Node {
  id: string
  type: NodeType
  position: Position
  label: string
  /**
   * Configuração específica do tipo de nó (será tipada por tipo no futuro).
   */
  config: {
    [k: string]: unknown
  }
}
/**
 * Posição do nó na grade isométrica, em células inteiras.
 */
export interface Position {
  x: number
  y: number
}
/**
 * Conexão dirigida de uma porta de saída para uma porta de entrada.
 */
export interface Edge {
  id: string
  source: EdgeEndpoint
  target: EdgeEndpoint
}
/**
 * Uma ponta de aresta: o nó e a porta dele.
 */
export interface EdgeEndpoint {
  node_id: string
  port: string
}
/**
 * Item da listagem: metadados sem o grafo completo.
 */
export interface WorkflowSummary {
  id: string
  name: string
  node_count: number
  edge_count: number
  created_at: string
  updated_at: string
}
/**
 * Corpo de `POST /api/workflows`. O grafo pode começar vazio.
 */
export interface WorkflowCreate {
  name: string
  /**
   * @maxItems 500
   */
  nodes?: Node[]
  /**
   * @maxItems 2000
   */
  edges?: Edge[]
}
/**
 * Corpo de `PUT /api/workflows/{id}`: substitui nome e grafo por completo.
 */
export interface WorkflowUpdate {
  name: string
  /**
   * @maxItems 500
   */
  nodes: Node[]
  /**
   * @maxItems 2000
   */
  edges: Edge[]
}
/**
 * Resposta de `GET /api/health`.
 *
 * `status` é `degraded` quando a API responde mas o banco não.
 */
export interface HealthStatus {
  status: 'ok' | 'degraded'
  database: 'ok' | 'unavailable'
  version: string
}
