import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = {
  title: 'TrajectoryLab',
  description: 'Trajectory-level evaluation for tool-using LLM agents',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased bg-gray-50 min-h-screen">
        <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-4">
          <Link
            href="/runs"
            className="text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors"
          >
            TrajectoryLab
          </Link>
          <span className="text-sm text-gray-400">
            trajectory-level evaluation for tool-using LLM agents
          </span>
        </nav>
        <main className="px-6 py-6">{children}</main>
      </body>
    </html>
  )
}
