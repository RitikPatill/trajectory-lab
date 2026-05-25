import type { Metadata } from 'next'
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
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
