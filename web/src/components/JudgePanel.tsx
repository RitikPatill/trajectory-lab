import type { VerdictOut } from '@/lib/types'

// --- Detail renderers per judge type ---

interface CriterionGrade {
  criterion_id: string
  score: number
  rationale: string
}

interface OutputResult {
  type: string
  value: unknown
  passed: boolean
}

function RubricDetails({ details }: { details: Record<string, unknown> }) {
  const grades = details.grades as CriterionGrade[] | undefined
  if (!grades || grades.length === 0) return null
  return (
    <ul className="mt-2 space-y-2">
      {grades.map((g) => (
        <li key={g.criterion_id} className="text-sm">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-700">{g.criterion_id}</span>
            <span
              className={`rounded px-1.5 py-0.5 text-xs font-semibold ${
                g.score >= 0.5
                  ? 'bg-green-100 text-green-700'
                  : 'bg-red-100 text-red-700'
              }`}
            >
              {(g.score * 100).toFixed(0)}%
            </span>
          </div>
          <p className="text-gray-500 mt-0.5">{g.rationale}</p>
        </li>
      ))}
    </ul>
  )
}

function TrajectoryDetails({ details }: { details: Record<string, unknown> }) {
  const checks: Array<{ label: string; key: string; invert?: boolean }> = [
    { label: 'Expected tools called', key: 'expected_tools_called' },
    { label: 'Max steps OK', key: 'max_steps_ok' },
    { label: 'Error loop detected', key: 'error_loop_detected', invert: true },
  ]

  return (
    <ul className="mt-2 space-y-1">
      {checks.map(({ label, key, invert }) => {
        const raw = details[key]
        if (raw === undefined) return null
        const value = Boolean(raw)
        const passed = invert ? !value : value
        return (
          <li key={key} className="flex items-center gap-2 text-sm">
            <span>{passed ? '✓' : '✗'}</span>
            <span className={passed ? 'text-gray-700' : 'text-red-600'}>
              {label}
            </span>
          </li>
        )
      })}
      {details.step_count !== undefined && (
        <li className="text-xs text-gray-400">
          Step count: {String(details.step_count)}
        </li>
      )}
      {Array.isArray(details.missing_tools) &&
        (details.missing_tools as string[]).length > 0 && (
          <li className="text-xs text-red-500">
            Missing tools: {(details.missing_tools as string[]).join(', ')}
          </li>
        )}
    </ul>
  )
}

function OutputDetails({ details }: { details: Record<string, unknown> }) {
  const results = details.results as OutputResult[] | undefined
  if (!results || results.length === 0) return null
  return (
    <ul className="mt-2 space-y-1">
      {results.map((r, i) => (
        <li key={i} className="flex items-center gap-2 text-sm">
          <span>{r.passed ? '✓' : '✗'}</span>
          <span className="font-mono text-xs bg-gray-100 rounded px-1">
            {r.type}
          </span>
          <span
            className="text-gray-600 truncate max-w-xs"
            title={String(r.value)}
          >
            {String(r.value).slice(0, 60)}
          </span>
        </li>
      ))}
    </ul>
  )
}

function VerdictCard({ verdict }: { verdict: VerdictOut }) {
  const title =
    verdict.judge.charAt(0).toUpperCase() + verdict.judge.slice(1) + ' Judge'
  const scorePct = (verdict.score * 100).toFixed(0)

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold text-gray-800">{title}</span>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-full px-2.5 py-0.5 text-sm font-medium ${
              verdict.passed
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {scorePct}%
          </span>
          <span className="text-base">{verdict.passed ? '✓' : '✗'}</span>
        </div>
      </div>

      <p className="mt-2 text-sm text-gray-600">{verdict.rationale}</p>

      {Object.keys(verdict.details).length > 0 && (
        <details className="mt-2">
          <summary className="cursor-pointer text-sm text-gray-400 hover:text-gray-600 select-none">
            Details
          </summary>
          {verdict.judge === 'rubric' && (
            <RubricDetails details={verdict.details} />
          )}
          {verdict.judge === 'trajectory' && (
            <TrajectoryDetails details={verdict.details} />
          )}
          {verdict.judge === 'output' && (
            <OutputDetails details={verdict.details} />
          )}
        </details>
      )}
    </div>
  )
}

interface JudgePanelProps {
  verdicts: VerdictOut[]
}

export default function JudgePanel({ verdicts }: JudgePanelProps) {
  if (!verdicts || verdicts.length === 0) {
    return (
      <div className="rounded border border-gray-200 p-4 text-sm text-gray-500">
        No judge verdicts available.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {verdicts.map((v, i) => (
        <VerdictCard key={i} verdict={v} />
      ))}
    </div>
  )
}
