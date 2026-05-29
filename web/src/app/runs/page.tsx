export const dynamic = 'force-dynamic'

import Link from 'next/link'
import { getRuns } from '@/lib/api'
import ScoreBadge from '@/components/ScoreBadge'

export default async function RunsPage() {
  const runs = await getRuns()

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Runs</h1>

      {runs.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500 text-sm">
            No runs yet. Start one with{' '}
            <code className="bg-gray-100 rounded px-1 py-0.5 text-xs">
              uv run tlab run --benchmark benchmarks/research --agent
              agents/research_v1.yaml
            </code>
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Run ID
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Agent ID
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Benchmark ID
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Date
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Cases
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Mean Score
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">
                  Pass Rate
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {runs.map((run) => {
                const passRate =
                  run.total_cases > 0
                    ? run.passed_cases / run.total_cases
                    : 0
                const date = new Date(run.created_at).toLocaleString()
                return (
                  <tr key={run.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <Link
                        href={`/runs/${run.id}`}
                        className="font-medium text-blue-600 hover:underline"
                      >
                        #{run.id}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-700">{run.agent_id}</td>
                    <td className="px-4 py-3 text-gray-700">
                      {run.benchmark_id}
                    </td>
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {date}
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {run.passed_cases}/{run.total_cases}
                    </td>
                    <td className="px-4 py-3">
                      {run.mean_score !== null ? (
                        <ScoreBadge
                          score={run.mean_score}
                          passed={run.mean_score >= 0.5}
                        />
                      ) : (
                        <span className="text-gray-400 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 rounded-full bg-gray-200 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-green-400"
                            style={{ width: `${(passRate * 100).toFixed(0)}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">
                          {(passRate * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
