/**
 * Typed fetch helpers for the TrajectoryLab FastAPI service.
 *
 * Base URL defaults to http://localhost:8000 (matches `tlab serve`).
 * Override by setting NEXT_PUBLIC_API_URL in .env.local.
 */

import type { CaseDetail, CompareOut, RunDetail, RunSummary } from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function getRuns(): Promise<RunSummary[]> {
  try {
    const res = await fetch(`${BASE_URL}/runs`, { cache: 'no-store' })
    if (!res.ok) return []
    return (await res.json()) as RunSummary[]
  } catch {
    return []
  }
}

export async function getRun(id: number): Promise<RunDetail | null> {
  try {
    const res = await fetch(`${BASE_URL}/runs/${id}`, { cache: 'no-store' })
    if (!res.ok) return null
    return (await res.json()) as RunDetail
  } catch {
    return null
  }
}

export async function getCase(
  runId: number,
  caseId: string
): Promise<CaseDetail | null> {
  try {
    const res = await fetch(
      `${BASE_URL}/runs/${runId}/cases/${encodeURIComponent(caseId)}`,
      { cache: 'no-store' }
    )
    if (!res.ok) return null
    return (await res.json()) as CaseDetail
  } catch {
    return null
  }
}

export async function getCompare(a: number, b: number): Promise<CompareOut | null> {
  try {
    const res = await fetch(`${BASE_URL}/compare?a=${a}&b=${b}`, { cache: 'no-store' })
    if (!res.ok) return null
    return (await res.json()) as CompareOut
  } catch {
    return null
  }
}
