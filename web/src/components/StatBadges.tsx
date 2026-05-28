interface StatBadgesProps {
  inputTokens: number
  outputTokens: number
  latencyMs: number
}

export default function StatBadges({
  inputTokens,
  outputTokens,
  latencyMs,
}: StatBadgesProps) {
  const latencySec = (latencyMs / 1000).toFixed(1)
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
        ↑ {inputTokens} tok
      </span>
      <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
        ↓ {outputTokens} tok
      </span>
      <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
        {latencySec} s
      </span>
    </div>
  )
}
