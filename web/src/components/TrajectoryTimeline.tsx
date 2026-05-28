import type { Step, Trajectory } from '@/lib/types'

function Pill({
  label,
  color,
}: {
  label: string
  color: string
}) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${color}`}
    >
      {label}
    </span>
  )
}

function TimelineNode({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex gap-4 pb-6">
      {/* vertical rail */}
      <div className="flex flex-col items-center">
        <div className="mt-1 h-3 w-3 rounded-full bg-gray-300 ring-2 ring-white" />
        <div className="flex-1 w-0.5 bg-gray-200" />
      </div>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  )
}

function StepNode({ step }: { step: Step }) {
  if (step.role === 'assistant') {
    const textBlocks = step.raw_content.filter((b) => b.type === 'text')
    return (
      <>
        {/* assistant text */}
        {textBlocks.length > 0 && (
          <TimelineNode>
            <div className="flex items-center gap-2 mb-1">
              <Pill label="Assistant" color="bg-blue-100 text-blue-800" />
              {(step.input_tokens > 0 || step.output_tokens > 0) && (
                <span className="text-xs text-gray-400">
                  {step.input_tokens}↑ {step.output_tokens}↓{' '}
                  {(step.latency_ms / 1000).toFixed(1)}s
                </span>
              )}
            </div>
            <div className="text-sm text-gray-700 whitespace-pre-wrap break-words">
              {textBlocks.map((b, i) => (
                <span key={i}>{b.text}</span>
              ))}
            </div>
          </TimelineNode>
        )}
        {/* tool calls */}
        {step.tool_calls.map((tc) => (
          <TimelineNode key={tc.tool_use_id}>
            <div className="flex items-center gap-2 mb-1">
              <Pill label={`Tool: ${tc.name}`} color="bg-orange-100 text-orange-800" />
            </div>
            <details className="text-sm">
              <summary className="cursor-pointer text-gray-500 hover:text-gray-700 select-none">
                Input JSON
              </summary>
              <pre className="mt-1 rounded bg-gray-50 p-2 text-xs overflow-x-auto break-words whitespace-pre-wrap">
                {JSON.stringify(tc.input, null, 2)}
              </pre>
            </details>
          </TimelineNode>
        ))}
      </>
    )
  }

  // role === 'tool'
  return (
    <>
      {step.tool_results.map((tr) => {
        const truncated =
          tr.content.length > 300
            ? tr.content.slice(0, 300) + '…'
            : tr.content
        const needsExpand = tr.content.length > 300
        return (
          <TimelineNode key={tr.tool_use_id}>
            <div className="flex items-center gap-2 mb-1">
              <Pill
                label={`Result: ${tr.name}`}
                color={
                  tr.is_error
                    ? 'bg-red-100 text-red-800'
                    : 'bg-purple-100 text-purple-800'
                }
              />
              {tr.is_error && (
                <span className="text-xs text-red-500 font-medium">ERROR</span>
              )}
            </div>
            {needsExpand ? (
              <details className="text-sm">
                <summary className="cursor-pointer text-gray-500 hover:text-gray-700 select-none">
                  {truncated}
                </summary>
                <div className="mt-1 text-gray-700 whitespace-pre-wrap break-words">
                  {tr.content}
                </div>
              </details>
            ) : (
              <div className="text-sm text-gray-700 whitespace-pre-wrap break-words">
                {tr.content}
              </div>
            )}
          </TimelineNode>
        )
      })}
    </>
  )
}

interface TrajectoryTimelineProps {
  trajectory: Trajectory
}

export default function TrajectoryTimeline({
  trajectory,
}: TrajectoryTimelineProps) {
  if (!trajectory || !trajectory.steps) {
    return (
      <div className="rounded border border-gray-200 p-4 text-sm text-gray-500">
        No trajectory data.
      </div>
    )
  }

  return (
    <div className="border-l-2 border-gray-200 pl-4 ml-4">
      {/* System prompt */}
      <TimelineNode>
        <div className="flex items-center gap-2 mb-1">
          <Pill label="System" color="bg-gray-200 text-gray-700" />
        </div>
        <details>
          <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700 select-none">
            System prompt (click to expand)
          </summary>
          <div className="mt-1 text-sm text-gray-700 whitespace-pre-wrap break-words">
            {trajectory.system}
          </div>
        </details>
      </TimelineNode>

      {/* Initial user messages */}
      {trajectory.initial_messages.map((msg, i) => {
        const content =
          typeof msg.content === 'string'
            ? msg.content
            : msg.content
                .filter((b) => b.type === 'text')
                .map((b) => b.text)
                .join('\n')
        return (
          <TimelineNode key={i}>
            <div className="flex items-center gap-2 mb-1">
              <Pill
                label={msg.role === 'user' ? 'User' : msg.role}
                color="bg-blue-50 text-blue-700"
              />
            </div>
            <div className="text-sm text-gray-700 whitespace-pre-wrap break-words">
              {content}
            </div>
          </TimelineNode>
        )
      })}

      {/* Steps */}
      {trajectory.steps.map((step) => (
        <StepNode key={step.index} step={step} />
      ))}

      {/* Final response */}
      {trajectory.final_response && (
        <TimelineNode>
          <div className="flex items-center gap-2 mb-1">
            <Pill label="Final" color="bg-green-100 text-green-800" />
          </div>
          <div className="text-sm text-gray-700 whitespace-pre-wrap break-words">
            {trajectory.final_response}
          </div>
        </TimelineNode>
      )}

      {/* Error */}
      {trajectory.error && (
        <TimelineNode>
          <div className="flex items-center gap-2 mb-1">
            <Pill label="Error" color="bg-red-100 text-red-800" />
          </div>
          <div className="text-sm text-red-700 font-mono break-words">
            {trajectory.error}
          </div>
        </TimelineNode>
      )}
    </div>
  )
}
