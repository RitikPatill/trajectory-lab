export const dynamic = 'force-dynamic'

import Link from 'next/link'
import { getCase } from '@/lib/api'
import ScoreBadge from '@/components/ScoreBadge'
import StatBadges from '@/components/StatBadges'
import TrajectoryTimeline from '@/components/TrajectoryTimeline'
import JudgePanel from '@/components/JudgePanel'

interface CaseDetailPageProps {
  params: { id: string; caseId: string }
}

export default async function CaseDetailPage({ params }: CaseDetailPageProps) {
  const runId = parseInt(params.id, 10)
  const caseId = decodeURIComponent(params.caseId)
  const data = await getCase(runId, caseId)

  if (!data) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <p className="text-red-700 font-medium">
          Case &quot;{caseId}&quot; not found in run #{runId}.
        </p>
        <Link
          href={`/runs/${runId}`}
          className="mt-2 inline-block text-sm text-blue-600 hover:underline"
        >
          ← Back to run
        </Link>
      </div>
    )
  }

  const traj = data.trajectory

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500 mb-4">
        <Link href="/runs" className="hover:text-blue-600 hover:underline">
          Runs
        </Link>
        <span className="mx-1">›</span>
        <Link
          href={`/runs/${runId}`}
          className="hover:text-blue-600 hover:underline"
        >
          Run #{runId}
        </Link>
        <span className="mx-1">›</span>
        <span className="text-gray-800 font-mono">{caseId}</span>
      </nav>

      {/* Header row */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-bold text-gray-900 font-mono">
              {caseId}
            </h1>
            <ScoreBadge score={data.aggregate_score} passed={data.passed} />
          </div>
          <p className="mt-2 text-sm text-gray-700 break-words">{data.task}</p>
        </div>

        {traj && (
          <StatBadges
            inputTokens={traj.total_input_tokens}
            outputTokens={traj.total_output_tokens}
            latencyMs={traj.total_latency_ms}
          />
        )}
      </div>

      {/* Inputs */}
      {Object.keys(data.inputs).length > 0 && (
        <details className="mb-6">
          <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800 select-none">
            Inputs
          </summary>
          <pre className="mt-2 rounded bg-gray-50 border border-gray-200 p-3 text-xs overflow-x-auto whitespace-pre-wrap break-words">
            {JSON.stringify(data.inputs, null, 2)}
          </pre>
        </details>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        {/* Trajectory timeline */}
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Trajectory
          </h2>
          <TrajectoryTimeline trajectory={traj} />
        </section>

        {/* Judge panel */}
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Judges
          </h2>
          <JudgePanel verdicts={data.verdicts} />
        </section>
      </div>
    </div>
  )
}
