'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import type { RunSummary } from '@/lib/types'

interface Props {
  runs: RunSummary[]
  currentA?: string
  currentB?: string
}

export default function ComparePicker({ runs, currentA, currentB }: Props) {
  const router = useRouter()
  const [selectedA, setSelectedA] = useState(currentA ?? '')
  const [selectedB, setSelectedB] = useState(currentB ?? '')

  function handleCompare() {
    if (!selectedA || !selectedB) return
    router.push(`/compare?a=${selectedA}&b=${selectedB}`)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 flex flex-wrap items-end gap-4">
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
          Run A
        </label>
        <select
          value={selectedA}
          onChange={(e) => setSelectedA(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[220px]"
        >
          <option value="">Select a run…</option>
          {runs.map((r) => (
            <option key={r.id} value={String(r.id)}>
              Run #{r.id} — {r.agent_id} / {r.benchmark_id}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
          Run B
        </label>
        <select
          value={selectedB}
          onChange={(e) => setSelectedB(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[220px]"
        >
          <option value="">Select a run…</option>
          {runs.map((r) => (
            <option key={r.id} value={String(r.id)}>
              Run #{r.id} — {r.agent_id} / {r.benchmark_id}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={handleCompare}
        disabled={!selectedA || !selectedB}
        className="px-4 py-1.5 rounded text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Compare
      </button>
    </div>
  )
}
