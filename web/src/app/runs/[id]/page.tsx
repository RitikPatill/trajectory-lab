export const dynamic = 'force-dynamic'

import Link from 'next/link'
import { getRun } from '@/lib/api'
import ScoreBadge from '@/components/ScoreBadge'

interface RunDetailPageProps {
  params: { id: string }
}

export default async function RunDetailPage({ params }: RunDetailPageProps) {
  const runId = parseInt(params.id, 10)
  const run = await getRun(runId)

  if (!run) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <p className="text-red-700 font-medium">Run #{runId} not found.</p>
        <Link href="/runs" className="mt-2 inline-block text-sm text-blue-600 hover:underline">
          ← Back to runs
        </Link>
      </div>
    )
  }

  const passRate =
    run.total_cases > 0 ? run.passed_cases / run.total_cases : 0

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500 mb-4">
        <Link href="/runs" className="hover:text-blue-600 hover:underline">
          Runs
        </Link>
        <span className="mx-1">›</span>
        <span className="text-gray-800">Run #{run.id}</span>
      </nav>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Run #{run.id}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Agent{' '}
            <span className="font-medium text-gray-700">{run.agent.name}</span>{' '}
            ({run.agent.model}) &middot; Benchmark{' '}
            <span className="font-medium text-gray-700">
              {run.benchmark.name}
            </span>{' '}
            &middot; {new Date(run.created_at).toLocaleString()}
          </p>
        </div>

        {/* Aggregate stats */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="text-center">
            <div className="text-xs text-gray-400 mb-1">Pass Rate</div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-24 rounded-full bg-gray-200 overflow-hidden">
                <div
                  className="h-full rounded-full bg-green-400"
                  style={{ width: `${(passRate * 100).toFixed(0)}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-700">
                {run.passed_cases}/{run.total_cases}
              </span>
            </div>
          </div>

          {run.mean_score !== null && (
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-1">Mean Score</div>
              <ScoreBadge
                score={run.mean_score}
                passed={run.mean_score >= 0.5}
              />
            </div>
          )}
        </div>
      </div>

      {/* Case grid */}
      {run.cases.length === 0 ? (
        <p className="text-sm text-gray-500">No cases in this run.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {run.cases.map((c) => (
            <Link
              key={c.case_id}
              href={`/runs/${run.id}/cases/${encodeURIComponent(c.case_id)}`}
              className="group rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-mono text-xs text-gray-500">
                  {c.case_id}
                </span>
                <ScoreBadge score={c.aggregate_score} passed={c.passed} />
              </div>
              <p className="mt-2 text-sm text-gray-700 line-clamp-2 break-words">
                {c.task}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
