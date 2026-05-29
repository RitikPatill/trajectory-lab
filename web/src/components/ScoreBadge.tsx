interface ScoreBadgeProps {
  score: number
  passed: boolean
}

export default function ScoreBadge({ score, passed }: ScoreBadgeProps) {
  const pct = (score * 100).toFixed(0)
  return passed ? (
    <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-sm font-medium text-green-800">
      {pct}% ✓
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-sm font-medium text-red-800">
      {pct}% ✗
    </span>
  )
}
