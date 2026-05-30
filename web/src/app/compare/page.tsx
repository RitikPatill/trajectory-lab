import { getCompare, getRuns } from '@/lib/api'
import ComparePicker from '@/components/ComparePicker'

export const dynamic = 'force-dynamic'

export default async function ComparePage({
  searchParams,
}: {
  searchParams: { a?: string; b?: string }
}) {
  const runs = await getRuns()
  const { a, b } = searchParams
  const compareData =
    a && b ? await getCompare(Number(a), Number(b)) : null

  const improved = compareData
    ? compareData.cases.filter((c) => c.delta > 0.001).length
    : 0
  const regressed = compareData
    ? compareData.cases.filter((c) => c.delta < -0.001).length
    : 0
  const unchanged = compareData
    ? compareData.cases.filter((c) => Math.abs(c.delta) <= 0.001).length
    : 0
  const meanDelta = compareData
    ? compareData.cases.reduce((sum, c) => sum + c.delta, 0) /
      (compareData.cases.length || 1)
    : 0

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Compare Runs</h1>

      <ComparePicker runs={runs} currentA={a} currentB={b} />

      {a && b && !compareData && (
        <p className="mt-6 text-red-600">
          Could not load comparison for runs {a} and {b}.
        </p>
      )}

      {compareData && (
        <div className="mt-6 space-y-6">
          {/* Summary header */}
          <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-wrap items-center gap-4">
            <span className="font-medium text-gray-700">
              Run&nbsp;A:&nbsp;
              <span className="font-semibold text-gray-900">
                {compareData.run_a.agent_id}
              </span>
            </span>
            <span className="text-gray-400">vs</span>
            <span className="font-medium text-gray-700">
              Run&nbsp;B:&nbsp;
              <span className="font-semibold text-gray-900">
                {compareData.run_b.agent_id}
              </span>
            </span>
            <div className="flex items-center gap-2 ml-auto flex-wrap">
              <span className="px-2 py-0.5 rounded text-sm font-medium bg-green-100 text-green-700">
                {improved} improved
              </span>
              <span className="px-2 py-0.5 rounded text-sm font-medium bg-red-100 text-red-700">
                {regressed} regressed
              </span>
              <span className="px-2 py-0.5 rounded text-sm font-medium bg-gray-100 text-gray-600">
                {unchanged} unchanged
              </span>
              <span
                className={`px-2 py-0.5 rounded text-sm font-medium ${
                  meanDelta > 0.001
                    ? 'bg-green-100 text-green-700'
                    : meanDelta < -0.001
                      ? 'bg-red-100 text-red-700'
                      : 'bg-gray-100 text-gray-600'
                }`}
              >
                Mean delta:{' '}
                {meanDelta >= 0 ? '+' : ''}
                {(meanDelta * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Diff table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-100 text-gray-600 text-left">
                  <th className="px-4 py-2 font-semibold">Case</th>
                  <th className="px-4 py-2 font-semibold text-right">Score A</th>
                  <th className="px-4 py-2 font-semibold text-right">Score B</th>
                  <th className="px-4 py-2 font-semibold text-right">Delta</th>
                  <th className="px-4 py-2 font-semibold text-center">A</th>
                  <th className="px-4 py-2 font-semibold text-center">B</th>
                </tr>
              </thead>
              <tbody>
                {compareData.cases.map((c) => {
                  const isImproved = c.delta > 0.001
                  const isRegressed = c.delta < -0.001
                  const rowClass = isImproved
                    ? 'bg-green-50'
                    : isRegressed
                      ? 'bg-red-50'
                      : 'bg-white'
                  const deltaClass = isImproved
                    ? 'text-green-600 font-medium'
                    : isRegressed
                      ? 'text-red-600 font-medium'
                      : 'text-gray-500'
                  const deltaStr =
                    (c.delta >= 0 ? '+' : '') + (c.delta * 100).toFixed(1) + '%'

                  return (
                    <tr
                      key={c.case_id}
                      className={`${rowClass} border-t border-gray-100`}
                    >
                      <td className="px-4 py-2 font-mono text-gray-800">
                        {c.case_id}
                      </td>
                      <td className="px-4 py-2 text-right text-gray-700">
                        {(c.score_a * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-2 text-right text-gray-700">
                        {(c.score_b * 100).toFixed(1)}%
                      </td>
                      <td className={`px-4 py-2 text-right ${deltaClass}`}>
                        {deltaStr}
                      </td>
                      <td className="px-4 py-2 text-center">
                        {c.passed_a ? (
                          <span className="text-green-600 font-bold">✓</span>
                        ) : (
                          <span className="text-red-500 font-bold">✗</span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-center">
                        {c.passed_b ? (
                          <span className="text-green-600 font-bold">✓</span>
                        ) : (
                          <span className="text-red-500 font-bold">✗</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
