import { apiRequest } from '../../api/client'
import type { WorkflowSummary } from '../../api/flowo.gen'

export async function fetchWorkflowSummaries(): Promise<WorkflowSummary[]> {
  // O corpo segue o contrato gerado do backend; não há validação em runtime por enquanto.
  return (await apiRequest('/api/workflows')) as WorkflowSummary[]
}
