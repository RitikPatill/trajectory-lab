/**
 * TypeScript interfaces mirroring the FastAPI Pydantic schemas
 * and the runner trace models.
 */

// --- Trajectory models (from tlab/runner/trace.py) ---

export interface ToolCall {
  tool_use_id: string
  name: string
  input: Record<string, unknown>
}

export interface ToolResult {
  tool_use_id: string
  name: string
  content: string
  is_error: boolean
}

export interface ContentBlock {
  type: string
  text?: string
  id?: string
  name?: string
  input?: Record<string, unknown>
  tool_use_id?: string
  content?: string
}

export interface Step {
  index: number
  role: 'assistant' | 'tool'
  raw_content: ContentBlock[]
  tool_calls: ToolCall[]
  tool_results: ToolResult[]
  input_tokens: number
  output_tokens: number
  latency_ms: number
  timestamp: string
}

export interface Trajectory {
  run_id: string
  model: string
  system: string
  initial_messages: Array<{ role: string; content: string | ContentBlock[] }>
  steps: Step[]
  final_response: string | null
  error: string | null
  total_input_tokens: number
  total_output_tokens: number
  total_latency_ms: number
  created_at: string
}

// --- API schemas (from tlab/api/schemas.py) ---

export interface AgentOut {
  id: number
  name: string
  model: string
  tools: string[]
  max_steps: number
}

export interface BenchmarkOut {
  id: number
  name: string
  description: string
  case_count: number
}

export interface VerdictOut {
  judge: string
  passed: boolean
  score: number
  rationale: string
  details: Record<string, unknown>
}

export interface CaseSummary {
  case_id: string
  task: string
  passed: boolean
  aggregate_score: number
}

export interface CaseDetail {
  case_id: string
  task: string
  inputs: Record<string, unknown>
  passed: boolean
  aggregate_score: number
  trajectory: Trajectory
  verdicts: VerdictOut[]
}

export interface RunSummary {
  id: number
  agent_id: number
  benchmark_id: number
  created_at: string
  total_cases: number
  passed_cases: number
  mean_score: number | null
}

export interface RunDetail {
  id: number
  agent: AgentOut
  benchmark: BenchmarkOut
  created_at: string
  total_cases: number
  passed_cases: number
  mean_score: number | null
  cases: CaseSummary[]
}

export interface CaseCompare {
  case_id: string
  score_a: number
  score_b: number
  delta: number
  passed_a: boolean
  passed_b: boolean
}

export interface CompareOut {
  run_a: RunSummary
  run_b: RunSummary
  cases: CaseCompare[]
}
