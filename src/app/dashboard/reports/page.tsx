import { BarChart3 } from 'lucide-react'

export default function ReportsPage() {
  return (
    <div className="animate-in">
      <div className="mb-6"><h1 className="text-2xl font-bold">Reports</h1><p className="text-sm text-[var(--text-muted)] mt-1">AI-generated insights and analytics.</p></div>
      <div className="card p-0 overflow-hidden">
        <div className="px-5 py-14 text-center">
          <BarChart3 className="w-10 h-10 text-[var(--text-muted)] mx-auto mb-3 opacity-20" />
          <p className="text-[14px] font-medium text-[var(--text-secondary)]">Reports coming soon</p>
          <p className="text-[12px] text-[var(--text-muted)] mt-1 max-w-sm mx-auto">AI-generated client status reports, engagement summaries, and activity analytics.</p>
        </div>
      </div>
    </div>
  )
}
